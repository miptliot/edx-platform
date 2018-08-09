import datetime

from .aws import *

# ==== Raven ====
RAVEN_CONFIG = AUTH_TOKENS.get('RAVEN_CONFIG', {})
if RAVEN_CONFIG:
    try:
        from raven.transport.requests import RequestsHTTPTransport
        RAVEN_CONFIG['transport'] = RequestsHTTPTransport
        INSTALLED_APPS += ( 'raven.contrib.django.raven_compat', )
    except ImportError:
        print 'could not enable Raven!'
# ===============

SSO_NPOED_URL = ENV_TOKENS.get('SSO_NPOED_URL')
if SSO_NPOED_URL:
    SSO_NPOED_URL = SSO_NPOED_URL.rstrip('/')

SSO_API_URL = '%s/api-edx/' % SSO_NPOED_URL
SSO_API_TOKEN = AUTH_TOKENS.get('SSO_API_TOKEN')


SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
SOCIAL_AUTH_LOGOUT_URL = '%s/logout/' % SSO_NPOED_URL
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

FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = FEATURES.get('PROCTORED_EXAMS_ATTEMPT_DELETE', False)

EDX_API_KEY = AUTH_TOKENS.get("EDX_API_KEY")
INSTALLED_APPS += (
    'open_edx_api_extension_cms',
)

TRACK_MAX_EVENT = 327680

# Used with XQueue
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds

FILE_UPLOAD_STORAGE_BUCKET_NAME = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_BUCKET_NAME', None)

if AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT'):
    AWS_S3_CALLING_FORMAT = AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT')

AWS_STORAGE_BUCKET_NAME = AUTH_TOKENS.get('AWS_STORAGE_BUCKET_NAME', 'edxuploads')

INSTALLED_APPS += (
    # Api extension for openedu
    'video_evms',
)

FEATURES['EVMS_TURN_ON'] = True
FEATURES["EVMS_QUALITY_CONTROL_ON"] = True

LOCALE_PATHS = (REPO_ROOT + "/npoed_translations", ) + LOCALE_PATHS

ORA_PATH_VENV = 'venvs/edxapp/lib/python2.7/site-packages/openassessment'
ORA_LOCALE_PATH = '{}/{}/locale'.format(PROJECT_ROOT.dirname().dirname(), ORA_PATH_VENV)
LOCALE_PATHS += (ORA_LOCALE_PATH,)

ORA_PATH_VENV = 'venvs/edxapp/src/ora2/openassessment'
ORA_LOCALE_PATH = '{}/{}/locale'.format(PROJECT_ROOT.dirname().dirname(), ORA_PATH_VENV)
LOCALE_PATHS += (ORA_LOCALE_PATH,)

PROCTOR_PATH_VENV = "venvs/edxapp/src/edx-proctoring/edx_proctoring"
PROCTOR_LOCALE_PATH = '{}/{}/locale'.format(PROJECT_ROOT.dirname().dirname(), PROCTOR_PATH_VENV)
LOCALE_PATHS += (PROCTOR_LOCALE_PATH,)

PLP_API_KEY = AUTH_TOKENS.get('PLP_API_KEY')
