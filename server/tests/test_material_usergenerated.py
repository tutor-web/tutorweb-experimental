import unittest

from tutorweb_quizdb.material.usergenerated import ug_render_data


class UgRenderDataTest(unittest.TestCase):
    maxDiff = None

    def test_ug_render_data(self):
        self.assertEqual(ug_render_data(dict(
            text="This is a question",
            explanation="Obvious, innit.",
            choice_correct="This is an answer",
            choice_incorrect=[
                "This is a wrong answer",
                "This is also a wrong answer",
                "",
                ""
            ]
        )), dict(
            content="""
<pre class="parse-as-tex">This is a question</pre>
<ol class="shuffle">
  <li><label><input type="radio" name="answer" value="472064795" />This is an answer</label></li>
  <li><label><input type="radio" name="answer" value="1917164105" />This is a wrong answer</label></li>
  <li><label><input type="radio" name="answer" value="2460721877" />This is also a wrong answer</label></li>
</ol>
            """.strip(),
            correct=dict(answer=['472064795']),
            tags=['type.question', 'review.mandatory'],
        ))
