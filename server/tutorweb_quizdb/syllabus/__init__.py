import urllib.parse

from sqlalchemy_utils import Ltree


def path_to_ltree(path_str):
    """Convert path param to an Ltree"""
    if path_str.startswith('nearest-tut:'):
        path = path_to_ltree(path_str.replace("nearest-tut:", ""))
        # We don't have an explicit concept of tutorial, but some conventions
        if path[0] == 'class':  # NB: We can't have zero-length LTrees
            return path[:4]  # e.g. class.ui.612.0
        return path[:3]  # e.g. comp.crypto251.0
    if path_str.startswith('/api/stage'):
        # Given a URL instead of a path, due to older client code. Unpack the path within
        path_str = urllib.parse.parse_qs(urllib.parse.urlparse(path_str).query)['path'][0]
        return path_to_ltree(path_str)
    # Default case, convert to Ltree
    return Ltree(path_str)


def includeme(config):
    config.include('tutorweb_quizdb.syllabus.results')
