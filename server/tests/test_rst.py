import unittest

from tutorweb_quizdb.rst import to_rst


class ToRstTest(unittest.TestCase):
    maxDiff = None

    def test_to_rst(self):
        self.assertEqual(to_rst("""
Moo
^^^

This is a *rubbish* example.
        """.strip()), """
<h1>Moo</h1><p>This is a <em>rubbish</em> example.</p>
        """.strip())

        self.assertEqual(to_rst("""
When :math`a \ne 0`, there are two solutions to :math:`ax^2 + bx + c = 0`
and they are

.. math::

   x = {-b \pm \sqrt{b^2-4ac} \over 2a}
        """.strip()), """
<p>When :math`a
e 0`, there are two solutions to <span class="math">\\(ax^2 + bx + c = 0\\)</span>
and they are</p><div class="math">\\begin{equation*}
x = {-b \\pm \\sqrt{b^2-4ac} \\over 2a}
\\end{equation*}</div>
        """.strip())

    def test_parsing_errors(self):
        """Errors get captured"""
        self.assertEqual(to_rst("""
.. parp

    Woo
        """.strip()), """
<b>Error: append() argument must be xml.etree.ElementTree.Element, not str</b>
        """.strip())
