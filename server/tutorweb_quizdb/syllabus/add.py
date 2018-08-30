"""
{
    "path": "comp.crypto251",
    "titles": ["Computer Science Department", "Cryptocurrency and the Smileycoin"],
    "requires_group": null,
    "lectures": [
        ["lec00100", "Introduction to cryptocurrencies"],
        ["lec00200", "Smileycoin basics"],
        ["lec00250", "Picking up a wallet"],
        ["lec00260", "Compiling the Linux wallet"],
        ["lec00300", "Introduction to the SMLY command line"],
        ["lec01400", "The transaction: from concept to theory"],
        ["lec01500", "The block and the blockchain"],
        ["lec01600", "Cryptocurrency mining"],
        ["lec02000", "Cryptography and cryptocurrencies"],
        ["lec02100", "Hash function introduction"],
        ["lec02200", "Elliptic curves"],
        ["lec03000", "The trilogy: tutor-web, Smileycoin and Education in a Suitcase"],
        ["lec03100", "The tutor-web premine"],
        ["lec03200", "Splitting the coinbase: No longer just a miners fee"],
        ["lec03400", "Staking"],
        ["lec03500", "The tutor-web as a faucet"],
        ["lec04000", "The command line in detail"],
        ["lec04500", "Building a transaction on the command line"],
        ["lec15000", "Cryptocurrency exchanges"],
        ["lec15500", "API access to exchanges"],
        ["lec26000", "Automation on the blockchain (stores, ATM, gambling etc)"],
        ["lec30000", "The Bitcoin programming language"],
        ["lec47000", "Atomic swaps"]
    ],
    "stage_template": [
        {
            "name": "stage0",
            "title": "write and review Examples",
            "material_tags": [{"path": 1}, "type.template", "outputtype.example"],
            "setting_spec": {}
        }
    ]
}
"""
import json

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession, Base, ACTIVE_HOST


def upsert_syllabus(path, title, href, requires_group):
    """Fetch / insert from the syllabus table something with path"""
    requires_group_fn = func.public.get_group_id(requires_group) if requires_group else None
    try:
        dbl = (DBSession.query(Base.classes.syllabus)
                        .filter_by(host_id=ACTIVE_HOST, path=path)
                        .one())
        dbl.title = title
        dbl.supporting_material_href = href
        dbl.requires_group_id = requires_group_fn
    except NoResultFound:
        dbl = Base.classes.syllabus(
            host_id=ACTIVE_HOST,
            path=path,
            title=title,
            supporting_material_href=href,
            requires_group_id=requires_group_fn,
        )
        DBSession.add(dbl)
    DBSession.flush()
    return dbl


def resolve_material_tags(stage_tmpl, db_lec):
    out = []

    for t in stage_tmpl['material_tags']:
        if isinstance(t, dict):
            if 'path' in t:
                out.append('path.%s.%s' % (
                    t['path'],
                    db_lec.path[-1],
                ))
        else:
            out.append(t)
    return out


def lec_import(tut_struct):
    # Make sure the department & tutorial are available
    path = Ltree(tut_struct['path'])
    for i in range(len(path)):
        tut_href = tut_struct.get('href', None) if (i == len(path) - 1) else None
        upsert_syllabus(path[:i + 1], tut_struct['titles'][i], tut_href, tut_struct.get('requires_group', None))

    # Add all lectures & stages
    for lec_name, lec_title, lec_href, *_unused_ in (l + [None, None] for l in tut_struct['lectures']):
        db_lec = upsert_syllabus(path + Ltree(lec_name), lec_title, lec_href, tut_struct.get('requires_group', None))

        # Get all current stages, put in dict
        db_stages = dict()
        for s in DBSession.query(Base.classes.stage).filter_by(syllabus=db_lec):
            db_stages[s.stage_name] = s

        for stage_tmpl in tut_struct['stage_template']:
            # De-mangle any functions in material tags
            material_tags = resolve_material_tags(stage_tmpl, db_lec)
            setting_spec = stage_tmpl['setting_spec'] or {}

            if stage_tmpl['name'] in db_stages:
                # If equivalent, do nothing
                # TODO: Is this doing the right thing?
                if db_stages[stage_tmpl['name']].material_tags == material_tags and \
                   db_stages[stage_tmpl['name']].stage_setting_spec == setting_spec:
                    if db_stages[stage_tmpl['name']].title != stage_tmpl['title']:
                        # Can just update title without needing a new version
                        db_stages[stage_tmpl['name']].title = stage_tmpl['title']
                        DBSession.flush()
                    continue
            # Add it, let the database worry about bumping version
            DBSession.add(Base.classes.stage(
                syllabus=db_lec,
                stage_name=stage_tmpl['name'],
                title=stage_tmpl['title'],
                material_tags=material_tags,
                stage_setting_spec=setting_spec
            ))
            DBSession.flush()


def multiple_lec_import(data):
    """Import a list of lectures, allowing previous lectures to define defaults"""
    if not isinstance(data, list):
        # Only one lecture, just import it
        lec_import(data)
        return

    for i in range(len(data)):
        # Lecture i should be a combination of itself and everything before it
        merged = {}
        for j in range(i + 1):
            merged.update(data[j])
        lec_import(merged)


def script():
    import argparse
    import sys
    from tutorweb_quizdb import setup_script

    argparse_arguments = [
        dict(description='Import a tutorial/lecture/stage configuration'),
        dict(
            name='infile',
            help='JSON syllabus file(s) to import, assumes STDIN if none given',
            type=argparse.FileType('r'),
            nargs='*',
            default=sys.stdin),
    ]

    with setup_script(argparse_arguments) as env:
        for f in env['args'].infile:
            multiple_lec_import(json.load(f))
