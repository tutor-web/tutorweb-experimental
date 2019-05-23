Tutor-web material format
*************************

Tutor-web content is stored in the ``db/material_bank`` directory,
a separate git repository storing question scripts.

Question format
===============

Questions are currently only written as R scripts that provide a question function.
Question scripts can be in any directory, but the file name should end with ``.q.R``.
An example script is below::

    # TW:PERMUTATIONS=10
    # TW:TAGS=type.question,preference.number
    # TW:TIMESANSWERED=0
    # TW:TIMESCORRECT=0
    question <- function(permutation, data_frames) {
        return(list(
            content = '
                <label>What is your favourite number? <input type="number" name="value" /></label>
            ',
            correct = list('value' = list(permutation))
        ))
    }

* ``TW:PERMUTATIONS=10`` indicates there are 10 variations of this question,
  which will be treated as separate questions. Which variant is required will
  be given to the question function.
* ``TW:TAGS=...`` lists the relevant tags for these questions, which will be
  used by stages when selecting relevant questions.
* ``TW:TIMESANSWERED=0/CORRECT=0`` gives an initial bias to the question stats,
  indicating how hard this question is.
* ``content`` is the raw HTML for the question. R helpers are available to
  generate this, and some special CSS classes will introduce behaviour, see
  "HTML Content reference".
* ``correct`` is a list of form values and the correct response. In the above
  case, the correct answer is the permutation, i.e. 1..10 depending on which
  permutation of the question is being used.

There are helper functions in ``Qgen/functions/functions.r`` to adapt older
scripts. In particular ``write_question`` will form a multiple-choice question
with the correct output::

    source("../../Qgen/functions/functions.r")
    question <- function(permutation, data_frames) {
        write_question(
            qid,
            qtitle,
            qtext,
            choices,
            choicescorrect,
            finalchoices,
            finalchoicescorrect,
            explain)
    }

Previewing material
===================

Your tutor-web user has to have the ``admin.material_render`` permission before being allowed to preview material.
You can add this at the commandline::

    echo username | ./server/bin/student_import --groups 'admin.material_render' -

You can then go to ``/preview`` and enter a path to a question you would like to preview.

Update
======

Before questions are available for tutor-web, you need to update the data base by running::

    ./server/bin/material_update

Data frames
===========

A question can require the student to fill in one or many tables before they
can answer questions. To do this:

1. Add a `HODF <https://github.com/shuttlethread/hodf>`__ table definition in a
   JSON file to the material bank, e.g. ``test.dataframe/heights.json``
2. At the top of any relevant question scripts, add
   ``#TW:DATAFRAMES=test.dataframe/heights.json`` to indicate the data needs to
   be collected.
3. When the question function is called, ``data_frames[['test.dataframe/heights.json']]``
   will contain the student's responses as a data.frame.

HTML Content reference
======================

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
