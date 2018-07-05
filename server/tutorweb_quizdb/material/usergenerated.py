import zlib

from mako.template import Template

from tutorweb_quizdb import DBSession, Base


UG_QUESTION = Template("""
<pre class="parse-as-tex">${text | h}</pre>
<ol class="shuffle">
  <li><label><input type="radio" name="answer" value="${digest_correct | h}" />${choice_correct | h}</label></li>
% for c in choice_incorrect:
  <li><label><input type="radio" name="answer" value="${digest_incorrect[loop.index] | h}" />${c | h}</label></li>
% endfor
</ol>
""")


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
        )
    return dict(
        content="<p>TODO:</p>",
        tags=['type.example', 'review.mandatory'],
    )
