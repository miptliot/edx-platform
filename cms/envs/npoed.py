import datetime

from .aws import *

# ==== Raven ====
RAVEN_CONFIG = AUTH_TOKENS.get('RAVEN_CONFIG', {})
RAVEN_DSN = ENV_TOKENS.get('RAVEN_DSN', None) # FIXME: for a smooth upgrade, remove in future
if RAVEN_CONFIG or RAVEN_DSN:
    try:
        from raven.transport.requests import RequestsHTTPTransport
        RAVEN_CONFIG['transport'] = RequestsHTTPTransport

        # ==== FIXME: for a smooth upgrade, remove in future
        if RAVEN_DSN:
            RAVEN_CONFIG['dsn'] = RAVEN_DSN
        # ====

        INSTALLED_APPS += ( 'raven.contrib.django.raven_compat', )
    except ImportError:
        print "couldn't enable Raven!"
# ===============

SSO_NPOED_URL = ENV_TOKENS.get('SSO_NPOED_URL')
if SSO_NPOED_URL:
    SSO_NPOED_URL = SSO_NPOED_URL.rstrip('/')

SSO_API_URL = "%s/api-edx/" % SSO_NPOED_URL
SSO_API_TOKEN = AUTH_TOKENS.get('SSO_API_TOKEN')


SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
SOCIAL_AUTH_LOGOUT_URL = "%s/logout/" % SSO_NPOED_URL
SOCIAL_AUTH_RAISE_EXCEPTIONS = True

MIDDLEWARE_CLASSES += (
    'sso_edx_npoed.middleware.SeamlessAuthorization',
)

PLP_URL = ENV_TOKENS.get('PLP_URL')
if PLP_URL:
    PLP_URL = PLP_URL.rstrip('/')

# We should login always with npoed-sso. There is specific backend for cms
# from sso_edx_npoed.backends.npoed import NpoedBackendCMS
# NpoedBackendCMS.name
SSO_NPOED_BACKEND_NAME = 'sso_npoed_cms-oauth2'
LOGIN_URL = '/auth/login/%s/' % SSO_NPOED_BACKEND_NAME

# Add extra dir for mako templates finder
# '/edx/app/edxapp/venvs/edxapp/src/npoed-sso-edx-client/sso_edx_npoed/templates'
NPOED_MAKO_TEMPLATES = ENV_TOKENS.get('NPOED_MAKO_TEMPLATES', [])

#TEMPLATE_DIRS.insert(0, '/edx/app/edxapp/venvs/edxapp/src/npoed-sso-edx-client/sso_edx_npoed')
MAKO_TEMPLATES['main'] = NPOED_MAKO_TEMPLATES + MAKO_TEMPLATES['main']


CELERYBEAT_SCHEDULE = {}

################### Third-party auth options ##################
#  copied from lms/aws.py
if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    THIRD_PARTY_AUTH_BACKENDS = ENV_TOKENS.get('THIRD_PARTY_AUTH_BACKENDS')

    if THIRD_PARTY_AUTH_BACKENDS:
        AUTHENTICATION_BACKENDS = THIRD_PARTY_AUTH_BACKENDS + list(AUTHENTICATION_BACKENDS)

    # The reduced session expiry time during the third party login pipeline. (Value in seconds)
    SOCIAL_AUTH_PIPELINE_TIMEOUT = ENV_TOKENS.get('SOCIAL_AUTH_PIPELINE_TIMEOUT', 600)

    # third_party_auth config moved to ConfigurationModels. This is for data migration only:
    THIRD_PARTY_AUTH_OLD_CONFIG = AUTH_TOKENS.get('THIRD_PARTY_AUTH', None)

    if ENV_TOKENS.get('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24) is not None:
        CELERYBEAT_SCHEDULE['refresh-saml-metadata'] = {
            'task': 'third_party_auth.fetch_saml_metadata',
            'schedule': datetime.timedelta(hours=ENV_TOKENS.get('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24)),
        }

EVMS_URL = ENV_TOKENS.get('EVMS_URL', None)
EVMS_API_KEY = AUTH_TOKENS.get('EVMS_API_KEY', None)

ROOT_URLCONF = 'sso_edx_npoed.cms_urls'

INSTALLED_APPS += ("openedx.core.djangoapps.video_evms", )
FEATURES["PROCTORED_EXAMS_ATTEMPT_DELETE"] = True

EDX_API_KEY = AUTH_TOKENS.get("EDX_API_KEY")
INSTALLED_APPS += (
    'open_edx_api_extension_cms',
)
