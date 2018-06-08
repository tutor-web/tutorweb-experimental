import base64
import random
import struct

import skippy

from tutorweb_quizdb import DBSession, Base


def get_allocation(settings, *args, **kwargs):
    name = settings.get('allocation_method', 'original')
    if name == 'original':
        return OriginalAllocation(settings, *args, **kwargs)
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

    def get_stats(self, old_stats):
        """
        Return updated stats structure, potentially allocating questions in process
        """
        if old_stats is None:
            material = self.get_material()
        else:
            material = self.from_public_id(x['uri'] for x in old_stats)

        out = []
        for m in material:
            # TODO: Should load 'em up in a temporary table
            (chosen, correct) = DBSession.query(Base.classes.answer_stats.chosen, Base.classes.answer_stats.correct).filter_by(
                stage_id=self.db_stage.stage_id,
                material_source_id=m[0],
            ).one()
            out.append(dict(
                uri=self.to_public_id(m[0], m[1]),
                chosen=chosen,
                correct=correct,
                online_only=False,  # TODO: How do we know?
                _type='regular',  # TODO: ...or historical?
            ))
        return out


class OriginalAllocation(BaseAllocation):
    def __init__(self, settings, db_stage, db_student):
        super(OriginalAllocation, self).__init__(settings, db_stage, db_student)
        self.seed = settings['allocation_seed']
        self.cipher = skippy.Skippy(settings['allocation_encryption_key'].encode('ascii'))
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
        # Is this a hist_sel lecture?
        hist_sel = 0  # TODO: float(settings.get('hist-sel', 0))
        if hist_sel > 0.00001:
            raise NotImplementedError("TODO: How do we do stage0 or stage1 or ...?")
        else:
            pass

        # Fetch all potential questions
        material = DBSession.execute(
            'SELECT material_source_id, permutation'
            ' FROM stage_material'
            ' WHERE stage_id = :stage_id'
            ' ORDER BY stage_id',
            dict(
                stage_id=self.db_stage.stage_id  # TODO: Or the historical ones
            )
        ).fetchall()

        # If there are enough, sample based on our seed
        if self.question_cap < len(material):
            local_random = random.Random()
            local_random.seed(self.seed)
            material = local_random.sample(material, self.question_cap)
        return material


class ExamAllocation(BaseAllocation):
    # TODO:
    pass
