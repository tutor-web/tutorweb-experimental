import logging

from sqlalchemy import Sequence

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.rst import to_rst
from tutorweb_quizdb.timestamp import timestamp_to_datetime, datetime_to_timestamp

log = logging.getLogger(__name__)


def mark_ug_reviews(db_a, settings, ug_reviews):
    """For a list of UG reviews, return a mark"""
    # Count / tally all review sections
    out_count = 0
    out_total = 0
    for reviewer_user_id, review in ug_reviews:
        if not review:
            continue

        review_total = 0
        for r_type, r_rating in review.items():
            if r_type == 'comments':
                continue
            try:
                review_total += int(r_rating)
            except ValueError:
                pass
        review['mark'] = review_total
        out_total += review_total
        out_count += 1

    if len(db_a.student_answer.get('text', '')) == 0:
        # Question isn't complete, so marked as far down as possible
        return -99
    if db_a.review and db_a.review.get('superseded', False):
        # If this is superseded, also mark down to get rid of it
        return -99
    if out_count > 0:
        # Mark should be mean of all reviews
        return out_total / max(int(settings.get('ugreview_minreviews', 3)), out_count)
    return 0


def db_to_incoming(alloc, db_a, ug_reviews):
    """Turn db entry back to wire-format"""
    def format_review(reviewer_user_id, review):
        """Format incoming review object from stage_ugmaterial for client"""
        if not review:
            review = {}

        # rst-ize comments
        if review.get('comments', None):
            review['comments'] = to_rst(review['comments'])
        return review

    return dict(
        uri=alloc.to_public_id(db_a.material_source_id, db_a.permutation),
        client_id=db_a.client_id,
        time_start=datetime_to_timestamp(db_a.time_start),
        time_end=datetime_to_timestamp(db_a.time_end),
        time_offset=db_a.time_offset,

        correct=db_a.correct,
        grade_after=float(db_a.grade),
        # NB: We don't return coins_awarded

        student_answer=db_a.student_answer,
        review=db_a.review,
        synced=True,
        mark=getattr(db_a, 'mark', 0),

        ug_reviews=[
            format_review(reviewer_user_id, review)
            for reviewer_user_id, review
            in ug_reviews
            if alloc.db_student.id != reviewer_user_id  # NB: Your own review will be in review, so no need
        ],
    )


def incoming_to_db(alloc, in_a):
    """Turn wire-format into a DB answer entry"""
    try:
        (mss_id, permutation) = alloc.from_public_id(in_a['uri'])
    except Exception as e:
        # Log exception along with real error
        log.exception("Could not parse question ID %s" % in_a['uri'])
        raise ValueError("Could not parse question ID %s" % in_a['uri'])
    ms = DBSession.query(Base.classes.material_source).filter_by(material_source_id=mss_id).one()

    if 'type.template' in ms.material_tags and permutation < 10:
        # It's newly-written material, rather than a review. Assign new permutation
        permutation = DBSession.execute(Sequence("ug_question_id"))

    return Base.classes.answer(
        stage_id=alloc.db_stage.stage_id,
        user_id=alloc.db_student.id,

        material_source_id=mss_id,
        permutation=permutation,
        client_id=in_a['client_id'],
        time_start=timestamp_to_datetime(in_a['time_start']),
        time_end=timestamp_to_datetime(in_a['time_end']),

        correct=in_a['correct'],
        grade=in_a['grade_after'],
        coins_awarded=0,

        student_answer=in_a.get('student_answer', None),
        review=in_a.get('review', None),
    )


def sync_answer_queue(alloc, in_queue, time_offset):
    # Lock answer_queue for this student, to stop any concorrent updates
    db_queue = (DBSession.query(Base.classes.answer)
                .filter(Base.classes.answer.stage_id == alloc.db_stage.stage_id)
                .filter(Base.classes.answer.user_id == alloc.db_student.id)
                .order_by(Base.classes.answer.time_end, Base.classes.answer.time_offset)
                .with_lockmode('update').all())

    # Fetch any reviews if we've written content here
    # NB: This won't select items in in_queue that haven't been inserted yet, but
    #     should just be the self-review we won't return anyway.
    stage_ug_reviews = {}
    for (mss_id, permutation, ug_reviews) in DBSession.execute(
            """
            SELECT material_source_id, permutation, reviews FROM stage_ugmaterial
             WHERE user_id = :user_id
               AND material_source_id IN (
                SELECT material_source_id FROM stage_material_sources sms
                 WHERE sms.stage_id = :stage_id
                   AND 'type.template' = ANY(sms.material_tags))
            ORDER BY time_end
            """, dict(
                stage_id=alloc.db_stage.stage_id,
                user_id=alloc.db_student.id,
            )):
        stage_ug_reviews[(mss_id, permutation)] = ug_reviews

    # First pass, fill in any missing time_offset fields
    for a in in_queue[:]:
        # If not complete, ignore it
        if not a.get('time_end', 0):
            in_queue.remove(a)
        if a.get('time_offset', None) is None:
            a['time_offset'] = time_offset
    # Re-sort based on any additional time_offsets
    in_queue.sort(key=lambda a: (a['time_end'], a['time_offset']))

    db_i = 0
    in_i = 0
    additions = 0
    out = []
    while True:
        if db_i >= len(db_queue):
            # Ran off the end of DB items, anything extra should be added to incoming
            cmp = -1

            if in_i >= len(in_queue):
                # Parsed both lists, done
                break
        elif in_i >= len(in_queue):
            # Ran off the end of incoming items, anything extra should be added to DB
            cmp = 1
        else:
            # Find smallest of DB/incoming entries
            cmp = in_queue[in_i]['time_end'] - datetime_to_timestamp(db_queue[db_i].time_end)
            if cmp == 0:
                cmp = in_queue[in_i]['time_offset'] - db_queue[db_i].time_offset

        if cmp == 0:
            # Matching items, update any review
            db_queue[db_i].review = in_queue[in_i].get('review', None)
            db_entry = db_queue[db_i]
            db_i += 1
            in_i += 1

        elif cmp < 0:
            # An extra incoming item, insert it
            db_entry = incoming_to_db(alloc, in_queue[in_i])
            db_entry.time_offset = time_offset
            DBSession.add(db_entry)
            additions += 1
            in_i += 1

        else:  # i.e. cmp < 0
            # An extra DB item, do nothing, will get added to outgoing list
            db_entry = db_queue[db_i]
            db_i += 1

        # If reviews are present, update DB entry based on them
        if (db_entry.material_source_id, db_entry.permutation) in stage_ug_reviews:
            db_entry.mark = mark_ug_reviews(db_entry, alloc.settings, stage_ug_reviews[(db_entry.material_source_id, db_entry.permutation)])
            if db_entry.mark > float(alloc.settings.get('ugreview_captrue', 3)):
                db_entry.correct = True
            elif db_entry.mark < float(alloc.settings.get('ugreview_capfalse', -1)):
                db_entry.correct = False
            else:
                db_entry.correct = None
        out.append(db_to_incoming(alloc, db_entry, stage_ug_reviews.get((db_entry.material_source_id, db_entry.permutation), [])))

        DBSession.flush()

    # Trigger work based on updated table
    # TODO: getCoinAward?
    # TODO: Review points for reviewed material?

    # Return combination of answer queues, and how many new entries we found
    return (out, additions)


def request_review(alloc):
    # Find a question that needs a review
    # Get all questions that we didn't write, ones with least reviews first
    for (mss_id, permutation, reviews) in DBSession.execute(
            """
            SELECT material_source_id, permutation, reviews FROM stage_ugmaterial
             WHERE user_id != :user_id
               AND correct IS NULL -- i.e. only ones for which a decision hasn't been reached
               AND material_source_id IN (
                SELECT material_source_id FROM stage_material_sources sms
                 WHERE sms.stage_id = :stage_id
                   AND 'type.template' = ANY(sms.material_tags))
            ORDER BY JSONB_ARRAY_LENGTH(reviews), RANDOM()
            """, dict(
                stage_id=alloc.db_stage.stage_id,
                user_id=alloc.db_student.id,
            )):

        # Consider all reviews
        mark = 0
        for (r_user_id, r_obj) in reviews:
            if r_obj is None:
                # Ignore empty reviews
                continue
            if r_user_id == alloc.db_student.id:
                # We reviewed it ourselves, so ignore it
                mark = -99
                break

        if mark >= 0:
            # This one is good enough for reviewing
            return dict(uri=alloc.to_public_id(mss_id, permutation))

    # No available material to review
    return dict()
