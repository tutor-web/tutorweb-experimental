import hashlib
import git
import os
import re

from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound

from tutorweb_quizdb import DBSession, Base


MATERIAL_BANK = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../db/material_bank'))  # TODO: This should be configured centrally, somewhere.


def file_md5sum(file):
    """
    MD5-sum of file
    """
    with open(os.path.join(MATERIAL_BANK, file), 'rb') as f:
        # TODO: Eugh
        # TODO: Not enough, what if we revert versions?
        content = f.read()

    return(hashlib.md5(content).hexdigest())


def file_metadata(file):
    """
    Read in all the metadata within the file
    """
    file_metadata = {}
    setting_re = re.compile(r'^[#]\s*TW:(\w+)=(.*)')
    with open(os.path.join(MATERIAL_BANK, file), 'r') as f:
        for line in f:
            m = setting_re.search(line)
            if m:
                file_metadata[m.group(1)] = m.group(2)
    return file_metadata


def update():
    """
    Ingest material from a given path and update database on it's existence
    """
    material_paths = {}
    for root, dirs, files in os.walk(MATERIAL_BANK):
        if '.git' in root:
            continue
        for f in files:
            if f.endswith('.q.R') or f.endswith('.e.R'):
                material_paths[os.path.join(os.path.relpath(root, MATERIAL_BANK), f)] = file_md5sum(os.path.join(root, f))


    # TODO: Having to be committed at least once is annoying
    for path, revision in material_paths.items():
        # Is this file/revision already here?
        already_here = False
        for m in DBSession.query(Base.classes.materialsource).filter_by(path=path, next_revision=None).all():
            if m.revision.strip() == revision.strip():
                already_here = True
            else:
                m.next_revision = revision
        if not already_here:
            metadata = file_metadata(path)
            DBSession.add(Base.classes.materialsource(
                path=path,
                revision=revision,
                permutationcount=int(metadata.get('QUESTIONS', 1)),
                materialtags=metadata.get('TAGS', '').split(','),
                dataframepaths=metadata.get('DATAFRAMES', '').split(','),  # TODO: Should path be relative?
            ))
        DBSession.flush()


def view_material_update(request):
    return update(**request.params)


def includeme(config):
    config.add_view(view_material_update, route_name='view_material_update', renderer='json')
    config.add_route('view_material_update', '/material/update')
