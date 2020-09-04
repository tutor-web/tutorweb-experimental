import decimal
import logging
import time

from lti import ToolConfig, ToolProvider, OutcomeRequest
from oauthlib.oauth1 import RequestValidator
from pyramid.httpexceptions import HTTPForbidden, HTTPFound
from pyramid.response import Response
from pyramid.security import remember

from tutorweb_quizdb import DBSession, Base
from tutorweb_quizdb.stage.utils import get_current_stage
from tutorweb_quizdb.student.create import create_student
from tutorweb_quizdb.syllabus import path_to_ltree


logger = logging.getLogger(__package__)
request_validator = None


class TwRequestValidator(RequestValidator):
    # Min/max length checks
    client_key_length = (3, 50)
    nonce_length = (13, 50)

    dummy_client = 'dummy_key'

    def __init__(self, secrets_db):
        self.secrets_db = secrets_db
        assert(self.dummy_client not in self.secrets_db)

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None, access_token=None):
        token = request_token or access_token or ''  # Just use one of them

        # Bin old nonces from table
        max_age = int(time.time()) - (60 * 15)
        DBSession.execute("DELETE FROM lti_nonce WHERE timestamp < :max_age", dict(
            max_age=max_age,
        ))

        if DBSession.query(Base.classes.lti_nonce).filter_by(
                client_key=client_key,
                timestamp=int(timestamp),
                nonce=nonce,
                token=token,
        ).count() > 0 or int(timestamp) < max_age:
            return False
        DBSession.add(Base.classes.lti_nonce(
            client_key=client_key,
            timestamp=int(timestamp),
            nonce=nonce,
            token=token,
        ))
        DBSession.flush()
        return True

    def validate_client_key(self, client_key, request):
        if client_key in self.secrets_db:
            return True
        logger.warning("Invalid client_key %s" % client_key)
        return False

    def get_client_secret(self, client_key, request):
        # NB: We always return something, even if client_key is invalid
        return self.secrets_db.get(client_key, 'dummy_secret')


class PyramidToolProvider(ToolProvider):
    """Pyramid request -> ToolProvider"""
    @classmethod
    def from_pyramid_request(cls, secret=None, request=None):
        if request is None:
            raise ValueError('request must be supplied')

        params = dict(request.POST.copy())
        for k in request.GET.keys():
            # request.POST includes query-string parameters(?)
            # Remove them to avoid confusing PyLTI
            del params[k]
        headers = dict(request.headers)
        url = request.url.replace('/auth/sso/', '/')  # Undo the rewrite in NGINX
        out = cls.from_unpacked_request(secret, params, url, headers)
        if secret is None:
            # NB: Otherwise we won't set the secret from the validator in is_valid_request()
            out.consumer_key = None
        return out


def sso(request):
    def get_param_fallback(*args):
        for a in args:
            if a is None:
                return None
            if a in request.params:
                return request.params[a]
        raise ValueError("None of %s found in request" % ",".join(args))

    # Validate user, get details
    tool_provider = PyramidToolProvider.from_pyramid_request(request=request)
    if not tool_provider.is_valid_request(request_validator):
        raise HTTPForbidden("Not a valid OAuth request")

    # Find any stage in the final query
    stage = get_current_stage(request, optional=True)

    # Create user if they don't exist
    (user, _) = create_student(
        request,
        user_name=get_param_fallback("custom_canvas_user_login_id", "lis_person_contact_email_primary", "user_id"),
        email=get_param_fallback("lis_person_contact_email_primary"),
        # Also have get_param_fallback("lis_person_name_full", None) if needed
        assign_password=True,  # They can reset if they need it
        group_names=['ltiuser.%s' % tool_provider.consumer_key],
        subscribe=[path_to_ltree('nearest-tut:%s' % stage.syllabus.path)] if stage else [],  # NB: subscribe will also auto-add groups (i.e. class)
    )

    if stage and tool_provider.is_outcome_service():
        # Store details for writing back grades as an outcome
        DBSession.merge(Base.classes.lti_sourcedid(
            user_id=user.user_id,
            stage_id=stage.stage_id,
            client_key=tool_provider.consumer_key,
            lis_outcome_service_url=tool_provider.lis_outcome_service_url,
            lis_result_sourcedid=tool_provider.lis_result_sourcedid,
        ))
        DBSession.flush()

    # Redirect to requested page
    return HTTPFound(
        headers=remember(request, user.id),
        location=request.path_qs.replace('/auth/sso/', '/'),
    )


def lti_replace_grade(stage, user, grade):
    """For given stage/user combo, try and update their grade in any LTI"""
    # Find any associated LTI with this stage/student
    sourcedid = DBSession.query(Base.classes.lti_sourcedid).filter_by(
        stage=stage,
        user=user
    ).first()
    if sourcedid is None:
        return
    grade_perc = decimal.Decimal("%1.4f" % (grade / 10.0))  # NB: Turn 0..10 grade into 0..1
    if sourcedid.last_perc is not None and grade_perc == sourcedid.last_perc:
        return  # Hasn't changed since last time

    # Post data to consumer
    outcome_resp = OutcomeRequest(opts=dict(
        consumer_key=sourcedid.client_key,
        consumer_secret=request_validator.get_client_secret(sourcedid.client_key, None),
        lis_outcome_service_url=sourcedid.lis_outcome_service_url,
        lis_result_sourcedid=sourcedid.lis_result_sourcedid,
    )).post_replace_result(grade_perc)

    # Report success / failure
    if outcome_resp.is_success():
        sourcedid.last_perc = grade_perc
        sourcedid.last_error = None
    else:
        logger.warning("Couldn't write back results to LTI: %s" % outcome_resp.description)
        # NB: outcome_resp.description is a lxml.objectify.StringElement, which sqlalchemy can't encode
        sourcedid.last_error = str(outcome_resp.description)
    DBSession.flush()


def view_tool_config(request):
    """Generate tool config and return"""
    lti_tool_config = ToolConfig(
        title="Tutor-web",
        launch_url=request.application_url,
        secure_launch_url=request.application_url.replace('http://', 'https://'),
        description="Responsive drilling platform",
        icon='%s/images/apple-touch-icon-ipad-retina-152x152.png' % request.application_url,
    )
    # See https://www.edu-apps.org/build_xml.html
    # https://www.edu-apps.org/extensions/index.html
    lti_tool_config.extensions['canvas.instructure.com'] = dict(
        domain=request.domain,  # We need tomain set so canvas associates any t-w URL with us
        tool_id='tutor-web',
        privacy_level='public',  # i.e. we want names & e-mail addresses
    )
    return Response(lti_tool_config.to_xml(), content_type='text/xml')


def includeme(config):
    def parse_secrets(s):
        out = dict()
        for line in s.split(','):
            if line:
                parts = line.split(':', 2)
                if len(parts) == 2:
                    out[parts[0]] = parts[1]
        return out

    config.add_view(sso, route_name='lti_sso')
    config.add_route('lti_sso', '/sso/*next_path')
    config.add_view(view_tool_config, route_name='lti_tool_config')
    config.add_route('lti_tool_config', '/lti-tool-config.xml')

    # Configure the request validator
    global request_validator
    request_validator = TwRequestValidator(parse_secrets(config.registry.settings.get('tutorweb.lti.secrets', '') or 'devel_key:devel_secret'))

    # Enable oAuth debugging
    # import oauthlib
    # import logging ; import sys
    # oauthlib.set_debug(True)
    # log = logging.getLogger('oauthlib')
    # log.addHandler(logging.StreamHandler(sys.stdout))
    # log.setLevel(logging.DEBUG)
