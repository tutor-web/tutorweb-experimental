import logging

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.timestamp import timestamp_to_datetime, datetime_to_timestamp

log = logging.getLogger(__name__)

# TODO: A SHA challenge based on (question_id:time_end) https://www.savjee.be/2017/09/Implementing-proof-of-work-javascript-blockchain/
#   - More blockchain-y
#   - Faking loads of entries becomes expensive
#   - Actually unique? Still have to use question_id:time_end:nonce
#   - How would you set difficulty in this case?
# ===> This is a (later) add-on, sealing the answer dict


def db_to_incoming(alloc, db_a):
    """Turn db entry back to wire-format"""
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
    )


def incoming_to_db(alloc, in_a):
    """Turn wire-format into a DB answer entry"""
    try:
        (mss_id, permutation) = alloc.from_public_id(in_a['uri'])
    except Exception as e:
        # Log exception along with real error
        log.exception("Could not parse question ID %s" % in_a['uri'])
        raise ValueError("Could not parse question ID %s" % in_a['uri'])

    return Base.classes.answer(
        stage_id=alloc.db_stage.stage_id,
        host_domain=alloc.db_student.host_domain,
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
                .filter(Base.classes.answer.host_domain == alloc.db_student.host_domain)
                .filter(Base.classes.answer.user_id == alloc.db_student.id)
                .order_by(Base.classes.answer.time_end, Base.classes.answer.time_offset)
                .with_lockmode('update').all())

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
            out.append(db_to_incoming(alloc, db_queue[db_i]))
            db_i += 1
            in_i += 1

        elif cmp < 0:
            # An extra incoming item, insert it
            db_entry = incoming_to_db(alloc, in_queue[in_i])
            db_entry.time_offset = time_offset
            DBSession.add(db_entry)
            out.append(db_to_incoming(alloc, db_entry))
            in_i += 1

        else:  # i.e. cmp < 0
            # An extra DB item, do nothing, will get added to outgoing list
            out.append(db_to_incoming(alloc, db_queue[db_i]))
            db_i += 1

        DBSession.flush()

    # Trigger work based on updated table
    # TODO: getCoinAward?
    # TODO: Review points for reviewed material?

    # Return combination of answer queues
    return out
