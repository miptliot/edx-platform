from aws import *

# ==== Raven ====
RAVEN_CONFIG = AUTH_TOKENS.get('RAVEN_CONFIG', {})
if RAVEN_CONFIG:
    try:
        from raven.transport.requests import RequestsHTTPTransport
        RAVEN_CONFIG['transport'] = RequestsHTTPTransport
        INSTALLED_APPS += ('raven.contrib.django.raven_compat', )
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

MIDDLEWARE_CLASSES += ('sso_edx_npoed.middleware.PLPRedirection',
                       'sso_edx_npoed.middleware.SeamlessAuthorization',)

PLP_URL = ENV_TOKENS.get('PLP_URL')
if PLP_URL:
    PLP_URL = PLP_URL.rstrip('/')

# We should login always with npoed-sso
SSO_NPOED_BACKEND_NAME = 'sso_npoed-oauth2'
LOGIN_URL = '/auth/login/%s/' % SSO_NPOED_BACKEND_NAME

# Add extra dir for mako templates finder
NPOED_MAKO_TEMPLATES = ENV_TOKENS.get('NPOED_MAKO_TEMPLATES', [])

MAKO_TEMPLATES['main'] = NPOED_MAKO_TEMPLATES + MAKO_TEMPLATES['main']

EVMS_URL = ENV_TOKENS.get('EVMS_URL', None)
EVMS_API_KEY = AUTH_TOKENS.get('EVMS_API_KEY', None)

ORA2_FILEUPLOAD_BACKEND = ENV_TOKENS.get('ORA2_FILEUPLOAD_BACKEND', 'filesystem')
ORA2_FILEUPLOAD_ROOT = ENV_TOKENS.get('ORA2_FILEUPLOAD_ROOT', '/edx/var/edxapp/ora2')
ORA2_FILEUPLOAD_CACHE_NAME = ENV_TOKENS.get('ORA2_FILEUPLOAD_CACHE_NAME', 'ora2_cache')

ROOT_URLCONF = 'sso_edx_npoed.lms_urls'

EXAMUS_PROCTORING_AUTH = AUTH_TOKENS.get('EXAMUS_PROCTORING_AUTH', {})

USERS_WITH_SPECIAL_PERMS_IDS_STR = ENV_TOKENS.get('USERS_WITH_SPECIAL_PERMS_IDS', [])
USERS_WITH_SPECIAL_PERMS_IDS = []
if USERS_WITH_SPECIAL_PERMS_IDS_STR:
    user_ids = USERS_WITH_SPECIAL_PERMS_IDS_STR.split(',')
    for user_id in user_ids:
        USERS_WITH_SPECIAL_PERMS_IDS.append(int(user_id))

PLP_API_KEY = AUTH_TOKENS.get('PLP_API_KEY')

PLP_BAN_ON = ENV_TOKENS.get('PLP_BAN_ON', False)

FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = FEATURES.get('PROCTORED_EXAMS_ATTEMPT_DELETE', False)

FEATURES['ICALENDAR_DUE_API'] = FEATURES.get('ICALENDAR_DUE_API', False)

ORA_PATH_VENV = 'venvs/edxapp/lib/python2.7/site-packages/openassessment'
ORA_LOCALE_PATH = '{}/{}/locale'.format(PROJECT_ROOT.dirname().dirname(), ORA_PATH_VENV)
LOCALE_PATHS += (ORA_LOCALE_PATH,)

TRACK_MAX_EVENT = 327680

if AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT'):
    AWS_S3_CALLING_FORMAT = AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT')

INSTALLED_APPS += (
    # Api extension for openedu
    'open_edx_api_extension',
    #'video_evms',
    'course_shifts',
)
FEATURES["ENABLE_COURSE_SHIFTS"] = True
FIELD_OVERRIDE_PROVIDERS += (
    'course_shifts.provider.CourseShiftOverrideProvider',
)

MAKO_TEMPLATES['main'] += []