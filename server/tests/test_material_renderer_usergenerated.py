import unittest

from tutorweb_quizdb.material.renderer.usergenerated import ug_render_data


class UgRenderDataTest(unittest.TestCase):
    maxDiff = None

    def test_ug_render_data(self):
        self.assertEqual(ug_render_data(dict(
            text="This is a **question**",
            explanation="Obvious, innit.",
            choice_correct="*This* is an answer",
            choice_incorrect=[
                "This is a *wrong* answer",
                "This is *also* a wrong answer",
                "",
                ""
            ]
        )), dict(
            content="""
<div><p>This is a <strong>question</strong></p></div>
<ol class="shuffle">
  <li><label><input type="radio" name="answer" value="1667303700" /><p><em>This</em> is an answer</p></label></li>
  <li><label><input type="radio" name="answer" value="2125222665" /><p>This is a <em>wrong</em> answer</p></label></li>
  <li><label><input type="radio" name="answer" value="1822426278" /><p>This is <em>also</em> a wrong answer</p></label></li>
</ol>
            """.strip(),
            correct=dict(answer=['1667303700']),
            tags=['type.question', 'review.mandatory'],
        ))

        self.assertEqual(ug_render_data(dict(
            text="This is a really good **example**",
        )), dict(
            content="""
<div><p>This is a really good <strong>example</strong></p></div>
            """.strip(),
            tags=['type.example', 'review.mandatory'],
        ))
