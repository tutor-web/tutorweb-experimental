import hashlib
import os.path
import re

import git


def parse_list(line):
    """
    Turn comma-separated (line) into a sequence of items, ignoring whitespace
    """
    for l in line.split(','):
        x = l.strip()
        if x:
            yield x


def file_md5sum(path):
    """
    Return MD5-sum string of file at (path)
    """
    with open(path, 'rb') as f:
        return(hashlib.md5(f.read()).hexdigest())


def _file_revision(material_bank, path, prev_revision):
    """
    Find out git revision for file, adding to it for each dirty version we see
    """
    # Get git revision for file
    repo = git.Repo(material_bank)
    git_revision = '(untracked)'
    for rev in repo.iter_commits(paths=path, max_count=1):
        git_revision = str(rev)

    m = re.search(r'^(.*)\+(\d+)$', prev_revision) if prev_revision else None
    if m and m.group(1) == git_revision:
        # The previous git revision is the same as this one, our count should be one higher
        rev_count = int(m.group(2) or '0') + 1
    elif prev_revision == git_revision:
        # We're part of the same revision, which was clean from git
        # NB: We know at this point the file is different, no point re-checking
        rev_count = 1
    else:
        # New revision, start from 1 if it's dirty
        is_dirty = repo.is_dirty(path=path, untracked_files=True)
        rev_count = 1 if is_dirty else 0

    # Add rev_count to git_revision if it's greater than zero
    return "%s+%d" % (git_revision, rev_count) if rev_count > 0 else git_revision


def path_to_materialsource(material_bank, path, prev_revision):
    """
    Read in metadata from file, turn into dict of options
    to create materialsource
    """
    file_metadata = dict(TAGS='')
    setting_re = re.compile(r'^[#]\s*TW:(\w+)=(.*)')
    try:
        with open(os.path.join(material_bank, path), 'r') as f:
            for line in f:
                m = setting_re.search(line)
                if m:
                    file_metadata[m.group(1)] = m.group(2)
        revision = _file_revision(material_bank, path, prev_revision)
    except FileNotFoundError:
        file_metadata = dict(
            QUESTIONS=0,
            TAGS='deleted',
        )
        revision = "(deleted)"

    # Add to tags based on file-name
    if path.endswith('.q.R'):
        file_metadata['TAGS'] += ',type.question'
    elif path.endswith('.e.R'):
        file_metadata['TAGS'] += ',type.example'

    return dict(
        path=os.path.normpath(path),
        revision=revision,
        permutationcount=int(file_metadata.get('QUESTIONS', 1)),
        materialtags=list(parse_list(file_metadata.get('TAGS', ''))),
        dataframepaths=list(parse_list(file_metadata.get('DATAFRAMES', ''))),  # TODO: Should path be relative?
    )
