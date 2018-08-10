import os

from tutorweb_quizdb import DBSession, Base

from tutorweb_quizdb.material.utils import path_tags, file_md5sum, path_to_materialsource


def update(material_bank):
    """
    Ingest material from a given path and update database on it's existence
    """
    # Generate dict of path => md5sum
    material_paths = {}
    for root, dirs, files in os.walk(material_bank):
        if '.git' in root:
            continue
        for f in files:
            if len(path_tags(f)) > 0:  # i.e. This file has a recognisable type, not just something to ignore
                material_paths[os.path.normpath(os.path.join(os.path.relpath(root, material_bank), f))] = file_md5sum(os.path.join(root, f))

    # For all paths in the database...
    for m in DBSession.query(Base.classes.material_source).filter_by(bank=material_bank, next_revision=None):
        if material_paths.get(m.path, None) != m.md5sum:
            # MD5sum changed (or file now nonexistant), add new materialsource entry
            new_m = Base.classes.material_source(**path_to_materialsource(material_bank, m.path, m.revision), md5sum=material_paths.get(m.path, None))
            DBSession.add(new_m)
            m.next_revision = new_m.revision

        # This path considered, remove from dict
        try:
            del material_paths[m.path]
        except KeyError:
            pass  # File doesn't exist, so nothing to remove

    # For any remaining paths, insert afresh into DB
    for path, md5sum in material_paths.items():
        DBSession.add(Base.classes.material_source(**path_to_materialsource(material_bank, path, None), md5sum=md5sum))
    DBSession.flush()


def view_material_update(request):
    return update(
        material_bank=request.registry.settings['tutorweb.material_bank.default'],
    )


def includeme(config):
    config.add_view(view_material_update, route_name='view_material_update', renderer='json')
    config.add_route('view_material_update', '/material/update')
