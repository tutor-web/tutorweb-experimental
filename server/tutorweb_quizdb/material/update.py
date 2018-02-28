import git
import os
import re

from pyramid.view import view_config

from tutorweb_quizdb import DBSession, Base


MATERIAL_BANK = '../db/material_bank'

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
    # Get git revision of all files in the material bank
    repo = git.Repo(MATERIAL_BANK)
    files = {}
    prev_files = {}
    for commit in repo.iter_commits():
        for file in commit.stats.files:
            if file not in files:
                files[file] = commit.hexsha
            elif file not in prev_files:
                prev_files[file] = commit.hexsha

    for path, revision in files.items():
        if path.endswith('.q.R'):
            # Is this file/revision already here?
            if DBSession.query(Base.classes.materialsource).filter_by(path=path, revision=revision).count() == 0:
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
