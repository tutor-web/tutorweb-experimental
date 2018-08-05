import os

import rpy2.robjects as robjects


def rob_to_dict(a):
    """
    Take R Object and turn it into something JSON-parsable
    """
    if isinstance(a, robjects.vectors.ListVector):
        if a.names:
            return dict(zip(a.names, [rob_to_dict(x) for x in a]))
        else:
            # No names, treat it as an array, combining vectors within
            out = []
            for x in a:
                out += rob_to_dict(x)
            return out
    else:
        return list(a)


def r_render(ms, permutation):
    """Execute R script to generate content"""
    # TODO: Caching of question objects?
    old_wd = os.getcwd()
    try:
        robjects.r('''question <- function () stop("R question script did not define a question function")''')
        robjects.r('''setwd''')(os.path.dirname(os.path.join(ms.bank, ms.path)))
        robjects.r('''source''')(os.path.basename(ms.path))
        # TODO: data.frames support

        rob = robjects.globalenv['question'](permutation, [])
        # TODO: Stacktraces?
        try:
            rv = rob_to_dict(rob)
        except Exception as e:
            raise ValueError("R question output not parsable %s\n%s" % (rob, e))

        if 'content' not in rv:
            raise ValueError("R question %s did not return 'content'" % ms.path)
        rv['content'] = "".join(rv['content'])
        return rv
    finally:
        os.chdir(old_wd)
