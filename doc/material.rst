Tutor-web material format
*************************

Content
=======

Various classes can be added to elements to trigger behaviour:

ol.shuffle
    Items within this list will be shuffled on display.

.parse-as-tex
    Parse the content of this element as LaTeX

span.math / div.math
    Parse the content as LaTeX math mode (used for rendered ReST)

.preview-as-tex / .preview-as-rst
    A preview is added below the textarea/input control with rendered markup.

.geogebra_applet
    Add a GeoGebra applet.

.reveal-on-answer
    This element won't be added on-screen until the student has answered this question.

Previewing material
===================

Your tutor-web user has to have the ``admin.material_render`` permission before being allowed to preview material.
You can add this at the commandline::

    echo username | sudo -H -unobody ./server/bin/student_import --groups 'admin.material_render' -

You can then go to ``/preview`` and enter a path to a question you would like to preview.
