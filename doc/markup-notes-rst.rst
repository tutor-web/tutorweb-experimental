Tutor-web Markup Cheat Sheet: ReST
==================================

Math mode
---------

You can use LaTeX equations within Restructured text

An in-line equation can be included using ``:math:``, e.g. ``:math:`x^2``` looks like :math:`x^2`

A larger equation can be included using ``.. math::``, e.g::

    .. math::

        \frac{ \sum_{t=0}^{N}f(t,k) }{N}

... looks like ...

.. math::

    \frac{ \sum_{t=0}^{N}f(t,k) }{N}

More information
----------------

The `docutils documentation <https://docutils.readthedocs.io/en/sphinx-docs/user/rst/cheatsheet.html#body-elements>`__
has more information on general markup.
