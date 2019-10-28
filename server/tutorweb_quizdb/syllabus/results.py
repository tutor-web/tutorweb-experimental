import collections

from sqlalchemy_utils import Ltree

from tutorweb_quizdb import DBSession


def result_summary(path=''):
    """Get a summary of all student grades for a syllabus item"""
    cols = set()
    data = collections.defaultdict(dict)
    for r in DBSession.execute("""
       SELECT DISTINCT ON (sy.path, st.stage_name, u.user_name)
              sy.path
              -- NB: We don't care about stage version, stage_names are constant
            , st.stage_name
            , u.user_name
            , a.grade
         FROM answer a
            , stage st
            , syllabus sy
            , "user" u
        WHERE a.stage_id = st.stage_id
          AND st.syllabus_id = sy.syllabus_id
          AND a.user_id = u.user_id
          AND sy.path <@ :path
     ORDER BY sy.path, st.stage_name, u.user_name, time_end DESC
    """, dict(
        path=path
    )):
        r = dict(r)
        # Make a user -> stage_path -> grade dict
        stage_path = str(r['path'] + Ltree(r['stage_name']))
        cols.add(stage_path)
        data[r['user_name']][stage_path] = r['grade']
    cols = sorted(cols)

    # Return as table
    yield ['student'] + cols
    for user_name, stages in sorted(data.items()):
        yield [user_name] + [stages.get(stage_path, 0) for stage_path in cols]


def result_full(path=''):
    """Get all student results for syllabus item"""
    yield ['lecture', 'stage', 'stage version', 'student', 'correct', 'grade', 'time']

    for r in DBSession.execute("""
       SELECT sy.path
            , st.stage_name
            , st.version stage_version
            , u.user_name
            , a.correct
            , a.grade
            , a.time_end
         FROM answer a
            , stage st
            , syllabus sy
            , "user" u
        WHERE a.stage_id = st.stage_id
          AND st.syllabus_id = sy.syllabus_id
          AND a.user_id = u.user_id
          AND sy.path <@ :path
     ORDER BY sy.path, st.stage_name, u.user_name, time_end
    """, dict(
        path=path,
    )):
        yield r


def script_syllabus_results():
    import csv
    import sys
    from tutorweb_quizdb import setup_script

    argparse_arguments = [
        dict(description='Return student results for a given tutorial/lecture path'),
        dict(
            name="--full",
            help="Return each results",
            action="store_true",
            default=False,
        ),
        dict(
            name='path',
            help='Tutorial/lecture path, return results from all stages within',
        ),
    ]

    with setup_script(argparse_arguments) as env:
        out_csv = csv.writer(sys.stdout)

        if env['args'].full:
            for r in result_full(env['args'].path):
                out_csv.writerow(r)
        else:
            for r in result_summary(env['args'].path):
                out_csv.writerow(r)
