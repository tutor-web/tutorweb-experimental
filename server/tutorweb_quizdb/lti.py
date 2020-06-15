import collections
import time

from lti import ToolConfig, ToolProvider
from oauthlib.oauth1 import RequestValidator
from pyramid.response import Response


request_validator = None


class TwRequestValidator(RequestValidator):
    # Min/max length checks
    client_key_length = (3, 50)
    nonce_length = (13, 50)

    nonce_db = set()
    NonceEntry = collections.namedtuple('NonceEntry', 'client_key timestamp nonce token')

    def __init__(self, secrets_db):
        self.start_time = int(time.time()) - 10  # 10 seconds ago
        self.secrets_db = secrets_db

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None, access_token=None):
        # Timeout any old entries first
        expiry_time = int(time.time()) - (60 * 15)  # 15 mins ago
        for n in self.nonce_db.copy():
            if n.timestamp < expiry_time:
                self.nonce_db.discard(n)

        n = self.NonceEntry(client_key, int(timestamp), nonce, request_token or access_token)
        if n.timestamp < self.start_time:
            # Nonce generated before we started, bin it to be safe
            return False
        if n in self.nonce_db:
            # Already been used, delete it
            return False
        self.nonce_db.add(n)
        return True

    def validate_client_key(self, client_key, request):
        return client_key in self.secrets_db

    def get_client_secret(self, client_key, request):
        # NB: We always return something, even if client_key is invalid
        return self.secrets_db.get(client_key, '')


class PyramidToolProvider(ToolProvider):
    """Pyramid request -> ToolProvider"""
    @classmethod
    def from_pyramid_request(cls, secret=None, request=None):
        if request is None:
            raise ValueError('request must be supplied')

        params = dict(request.POST.copy())
        headers = dict(request.headers)
        url = request.url
        return cls.from_unpacked_request(secret, params, url, headers)


def sso(request):
    def get_param_fallback(*args):
        for a in args:
            if a is None:
                return None
            if a in request.params:
                return request.params[a]
        raise ValueError("None of %s found in request" % ",".join(args))

    tool_provider = PyramidToolProvider.from_pyramid_request(request=request)
    if tool_provider.is_valid_request(request_validator):
        user_handle = get_param_fallback("custom_canvas_user_login_id", "lis_person_contact_email_primary", "user_id")
        user_email = get_param_fallback("lis_person_contact_email_primary")
        user_full_name = get_param_fallback("lis_person_name_full", None)
    else:
        user_handle = 'invalid'
        user_email = 'invalid'
        user_full_name = 'invalid'

    return Response(" ".join((
        user_handle,
        user_email,
        user_full_name,
    )), content_type='text/plain')


def tool_config(request):
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
        tool_id='tutor-web',
        privacy_level='public',  # i.e. we want names & e-mail addresses
        course_navigation=dict(
            enabled="true",
            url=request.application_url,
            text="Hello",
        ),
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
    config.add_route('lti_sso', '/sso')
    config.add_view(tool_config, route_name='lti_tool_config')
    config.add_route('lti_tool_config', '/tool-config.xml')

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
