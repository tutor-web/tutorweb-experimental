import colander
import deform
from deform.schema import CSRFSchema
import deform.widget as widget
from bag.text import strip_preparer, strip_lower_preparer


def _(s):
    """No translations, yet"""
    return s


def user_to_data(user):
    return dict(
        handle=user.user_name,
        email=user.email,
    )


class LoginSchema(CSRFSchema):
    handle = colander.SchemaNode(
        colander.String(), title=_('User name'), preparer=strip_preparer)
    password = colander.SchemaNode(colander.String(), widget=widget.PasswordWidget())


class RegisterSchema(CSRFSchema):
    handle = colander.SchemaNode(
        colander.String(), title=_('User name'), preparer=strip_preparer)
    email = colander.SchemaNode(
        colander.String(), title=_('Email'), description=_('Enter your preferred e-mail address, which we will use for notifications.'),
        preparer=strip_lower_preparer,
        validator=colander.Email(),
        widget=widget.TextInputWidget(
            size=40, maxlength=260, type='email', placeholder=_("joe@example.com")))


class ActivateRequestSchema(CSRFSchema):
    email = colander.SchemaNode(
        colander.String(), title=_('Email'), description=_('Enter your e-mail address.'),
        preparer=strip_lower_preparer,
        validator=colander.Email(),
        widget=widget.TextInputWidget(
            size=40, maxlength=260, type='email', placeholder=_("joe@example.com")))


class ActivateFinalizeSchema(CSRFSchema):
    handle = colander.SchemaNode(
        colander.String(), title=_('User name'), preparer=strip_preparer,
        missing='',  # NB: Defeat validation on submit
        widget=widget.TextInputWidget(readonly=True))
    password = colander.SchemaNode(
        colander.String(), title=_('Password'), validator=colander.Length(min=6),
        widget=widget.CheckedPasswordWidget())


class ProfileSchema(CSRFSchema):
    handle = colander.SchemaNode(
        colander.String(), title=_('User name'), preparer=strip_preparer,
        missing='',  # NB: Defeat validation on submit
        widget=widget.TextInputWidget(readonly=True))
    email = colander.SchemaNode(
        colander.String(), title=_('Email'), description=_('Enter your preferred e-mail address, which we will use for notifications.'),
        preparer=strip_lower_preparer,
        validator=colander.Email(),
        widget=widget.TextInputWidget(
            size=40, maxlength=260, type='email', placeholder=_("joe@example.com")))


def process_form(request, schema, error=None, buttons=('submit',), init_data=None):
    form = deform.Form(schema().bind(request=request), buttons=buttons)

    if not error and request.method == 'POST':
        try:
            captured = form.validate(request.POST.items())
            captured['_is_form_data'] = True
            return captured
        except deform.exception.ValidationFailure as e:
            # Render error form
            return dict(
                render_flash_messages=lambda: "",  # TODO:
                form=e.render(),
            )

    return dict(
        render_flash_messages=lambda: error or "",  # TODO:
        form=form.render(init_data or {}),
    )
