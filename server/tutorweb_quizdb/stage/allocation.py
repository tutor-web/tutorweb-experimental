import base64
import random
import struct

import skippy

from tutorweb_quizdb import DBSession


def get_allocation(settings, *args, **kwargs):
    name = settings.get('allocation_method', 'original')
    if name == 'original':
        return OriginalAllocation(settings, *args, **kwargs)
    elif name == 'passthrough':
        return PassThroughAllocation(settings, *args, **kwargs)
    elif name == 'exam':
        return ExamAllocation(settings, *args, **kwargs)
    else:
        raise ValueError("Unknown allocation module %s" % name)


class BaseAllocation():
    def __init__(self, settings, db_stage, db_student):
        self.settings = settings
        self.db_stage = db_stage
        self.db_student = db_student

    def get_material(self, ids=None, stats=False):
        """
        Return list of dicts, e.g.
            dict(public_id=(id user sees), ms=(ms object), permutation=p, chosen=x, correct=y)

        ...chosen & correct only required if stats=True
        """
        raise NotImplemented

    def to_public_id(self, mss_id, permutation):
        """
        Turn (mss_id, permutation) into a public question ID
        """
        return '%d:%d' % (mss_id, permutation)

    def from_public_id(self, public_id):
        """
        Turn the public ID back into a (mss_id, permutation) tuple
        """
        return tuple(int(x) for x in public_id.split(":", 1))

    def get_stats(self, material):
        """
        Return stats for each item in material, (mss_id, permutation) tuples
        """
        out = []
        for m in material:
            # TODO: Terribly inefficient
            rs = DBSession.execute(
                'SELECT chosen, correct'
                ' FROM answer_stats'
                ' WHERE stage_id = :stage_id'
                ' AND material_source_id = :mss_id'
                '',
                dict(
                    stage_id=self.db_stage.stage_id,
                    mss_id=m[0],  # NB: For stats purposes, we consider all permutations equal
                )
            ).fetchone()
            out.append(dict(
                uri=self.to_public_id(m[0], m[1]),
                chosen=rs[0] if rs else 0,
                correct=rs[1] if rs else 0,
                online_only=False,  # TODO: How do we know?
                _type='regular',  # TODO: ...or historical?
            ))
        return out

    def should_refresh_questions(self, aq, old_aq):
        """
        Has enough time passed between 2 answer queues that we should refresh
        the student's question bank?
        """
        return False


class OriginalAllocation(BaseAllocation):
    def _aq_length(self):
        # Get length of answerQueue
        return DBSession.execute(
            'SELECT COUNT(*)'
            ' FROM answer'
            ' WHERE stage_id = :stage_id'
            '   AND user_id = :user_id'
            '',
            dict(
                stage_id=self.db_stage.stage_id,
                user_id=self.db_student.user_id,
            )
        ).fetchone()[0]

    def __init__(self, settings, db_stage, db_student):
        super(OriginalAllocation, self).__init__(settings, db_stage, db_student)
        self.seed = int(settings['allocation_seed'])
        self.cipher = skippy.Skippy(settings['allocation_encryption_key'].encode('ascii'))
        self.refresh_int = int(self.settings.get('allocation_refresh_interval', 20))
        self.question_cap = 100

    def to_public_id(self, mss_id, permutation):
        return base64.b64encode(struct.pack(
            'II',
            self.cipher.encrypt(mss_id),
            self.cipher.encrypt(permutation),
        )).decode('ascii')

    def from_public_id(self, public_id):
        return tuple(
            self.cipher.decrypt(x)
            for x
            in struct.unpack('II', base64.b64decode(public_id))
        )

    def get_material(self, ids=None, stats=False):
        # Fetch all potential questions
        material = DBSession.execute(
            'SELECT material_source_id, permutation'
            ' FROM stage_material'
            ' WHERE stage_id = :stage_id'
            ' ORDER BY stage_id',
            dict(
                stage_id=self.db_stage.stage_id
            )
        ).fetchall()

        # If there are enough, sample based on our seed & how many questions student has answered
        if self.question_cap < len(material):
            local_random = random.Random()
            local_random.seed(self.seed + (self._aq_length() // self.refresh_int))
            material = local_random.sample(material, self.question_cap)
        return material

    def should_refresh_questions(self, aq, additions):
        """
        Has enough time passed between 2 answer queues that we should refresh
        the student's question bank?
        """
        return len(aq) // self.refresh_int != (len(aq) - additions) // self.refresh_int


class PassThroughAllocation(BaseAllocation):
    """
    Public IDs are '(question_path):(permutation)', return all questions.
    To make things obvious when unit testing.

    Also set allocation_bank_name to the material bank in question
    """
    def __init__(self, settings, db_stage, db_student):
        super(PassThroughAllocation, self).__init__(settings, db_stage, db_student)
        self.bank = settings['allocation_bank_name']

    def to_public_id(self, mss_id, permutation):
        """
        Turn (mss_id, permutation) into a public question ID
        """
        (mss_path,) = DBSession.execute(
            'SELECT path'
            ' FROM material_source'
            ' WHERE material_source_id = :mss_id'
            '   AND next_revision IS NULL',
            dict(
                mss_id=mss_id,
            )
        ).fetchone()

        return '%s:%d' % (mss_path, permutation)

    def from_public_id(self, public_id):
        """
        Turn the public ID back into a (mss_id, permutation) tuple
        """
        (mss_path, permutation) = public_id.split(":", 1)
        (mss_id,) = DBSession.execute(
            'SELECT material_source_id'
            ' FROM material_source'
            ' WHERE bank = :bank'
            '   AND path = :path'
            '   AND next_revision IS NULL',
            dict(
                bank=self.bank,
                path=mss_path,
            )
        ).fetchone()
        return (mss_id, int(permutation),)

    def get_material(self, ids=None, stats=False):
        """
        Fetch all potential questions, no filter.
        """
        material = DBSession.execute(
            'SELECT material_source_id, permutation'
            ' FROM stage_material'
            ' WHERE stage_id = :stage_id'
            ' ORDER BY stage_id',
            dict(
                stage_id=self.db_stage.stage_id
            )
        ).fetchall()
        return material


class ExamAllocation(BaseAllocation):
    # TODO:
    pass
