import zlib

from mako.template import Template

from tutorweb_quizdb import DBSession, Base


UG_QUESTION = Template("""
<%! from tutorweb_quizdb.rst import to_rst %>
<div>${text | to_rst}</div>
<ol class="shuffle">
  <li><label><input type="radio" name="answer" value="${digest_correct | h}" />${choice_correct | to_rst}</label></li>
% for c in choice_incorrect:
  <li><label><input type="radio" name="answer" value="${digest_incorrect[loop.index] | h}" />${c | to_rst}</label></li>
% endfor
% if context.get('explanation', UNDEFINED):
  <div class="reveal-on-answer explanation">${explanation | to_rst}</div>
% endif
</ol>
""")


UG_QUESTION_REVIEW = [
    dict(
        name='content', title='Content',
        values=[
            [-12, "The content is irrelevant"],
            [-12, "There is a mistake in the formulation of the problem or the answer"],
            [3, "The question is correctly formulated. It does not seem that the question writer put much thought into it"],
            [4, "The question is correctly formulated. It seems that the question writer put a lot of thought into it"],
        ]
    ),
    dict(
        name='understanding', title='Understanding',
        values=[
            [1, "Answering the question correctly does not require any understanding of the subject, just routine calculation"],
            [2, "Answering the question correctly requires some understanding of the subject but is mostly routine calculation"],
            [3, "Answering the question correctly requires understanding of the subject"],
            [4, "Answering the question correctly requires deep understanding of the subject"],
        ]
    ),
    dict(
        name='presentation', title='Presentation',
        values=[
            [-12, "There is more than one spelling/grammar mistakes in the question"],
            [0, "There is one spelling/grammar mistake in the question"],
            [3, "There are no spelling/grammar mistakes in the questions but it could be phrased better"],
            [4, "There are no spelling/grammar mistakes in the question and it is well phrased"],
        ]
    ),
    dict(
        name='difficulty', title='Difficulty',
        values=[
            [0, "The question is very easy"],
            [3, "The question is quite easy"],
            [3, "The question is quite difficult"],
            [4, "The question is very difficult"],
        ]
    ),
]

UG_EXAMPLE = Template("""
<%! from tutorweb_quizdb.rst import to_rst %>
% if context.get('title', UNDEFINED) is not UNDEFINED:
    <h3>${title | h}</h3>
% endif
<div>${text | to_rst}</div>
""")


UG_EXAMPLE_REVIEW = [
    dict(
        name='content', title='Content',
        values=[
            [-12, "The content is irrelevant"],
            [-12, "There is a mistake in the formulation of the problem or the answer"],
            [3, "The example is correctly formulated. It does not seem that the example writer put much thought into it"],
            [4, "The example is correctly formulated. It seems that the example writer put a lot of thought into it"],
        ]
    ),
    dict(
        name='presentation', title='Presentation',
        values=[
            [-12, "There is more than one spelling/grammar mistakes in the example"],
            [0, "There is one spelling/grammar mistake in the example"],
            [3, "There are no spelling/grammar mistakes in the examples but it could be phrased better"],
            [4, "There are no spelling/grammar mistakes in the example and it is well phrased"],
        ]
    ),
    dict(
        name='difficulty', title='Difficulty',
        values=[
            [0, "The example is very easy"],
            [3, "The example is quite easy"],
            [3, "The example is quite difficult"],
            [4, "The example is very difficult"],
        ]
    ),
]


def ug_render(ms, permutation):
    (data,) = DBSession.query(Base.classes.answer.student_answer).filter_by(
        material_source_id=ms.material_source_id,
        permutation=permutation,
    ).order_by(Base.classes.answer.answer_id).first()
    return ug_render_data(data)


def ug_render_data(data):
    """Turn student answer into material dict"""
    if 'choice_correct' in data:
        # It's a question
        data['digest_correct'] = zlib.crc32(data['choice_correct'].encode('utf8'))
        data['choice_incorrect'] = [x for x in data['choice_incorrect'] if x]
        data['digest_incorrect'] = [zlib.crc32(x.encode('utf8')) for x in data['choice_incorrect']]
        return dict(
            content=UG_QUESTION.render(**data).strip(),
            correct=dict(answer=[str(data['digest_correct'])]),
            tags=['type.question', 'review.mandatory'],
            review_questions=UG_QUESTION_REVIEW,
        )
    return dict(
        content=UG_EXAMPLE.render(**data).strip(),
        tags=['type.example', 'review.mandatory'],
        review_questions=UG_EXAMPLE_REVIEW,
    )
