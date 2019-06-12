from django.utils.translation import ugettext_lazy as _

from aws import *
from openedx.eduscaled.common.docker import is_docker
from openedx.eduscaled.common.edxlogging import get_patched_logger_config

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

ENV_SYSLOG_USE_TCP = str(os.getenv('SYSLOG_USE_TCP', False)) == 'True'
ENV_SYSLOG_HOST = os.getenv('SYSLOG_HOST', None)
ENV_SYSLOG_PORT = int(os.getenv('SYSLOG_PORT', 0))
ENV_SYSLOG_SOCKET_TIMEOUT = float(os.getenv('SYSLOG_SOCKET_TIMEOUT', 0))

log_settings = {
    'syslog_use_tcp': ENV_TOKENS.get('SYSLOG_USE_TCP', ENV_SYSLOG_USE_TCP),
    'syslog_host': ENV_TOKENS.get('SYSLOG_HOST', ENV_SYSLOG_HOST),
    'syslog_port': int(ENV_TOKENS.get('SYSLOG_PORT', ENV_SYSLOG_PORT)),
    'syslog_socket_timeout': float(ENV_TOKENS.get('SYSLOG_SOCKET_TIMEOUT', ENV_SYSLOG_SOCKET_TIMEOUT))
}

if is_docker():
    get_patched_logger_config(
        LOGGING,
        log_dir="/tmp",  # FIXME
        service_variant=SERVICE_VARIANT,
        use_raven=bool(RAVEN_CONFIG),
        use_stsos=True,
        log_settings=log_settings
    )

SSO_TP_URL = ENV_TOKENS.get('SSO_TP_URL')
if SSO_TP_URL:
    SSO_TP_URL = SSO_TP_URL.rstrip('/')

SSO_API_URL = '%s/api-edx/' % SSO_TP_URL
SSO_API_TOKEN = AUTH_TOKENS.get('SSO_API_TOKEN')

# for the branch hawthorn_saas_docker must be True by default
SSO_PUSH_CHANGES = ENV_TOKENS.get('SSO_PUSH_CHANGES', True)

SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
SOCIAL_AUTH_LOGOUT_URL = '%s/logout/' % SSO_TP_URL
SOCIAL_AUTH_RAISE_EXCEPTIONS = True

MIDDLEWARE_CLASSES += ('sso_edx_tp.middleware.SeamlessAuthorization',)

PLP_URL = ENV_TOKENS.get('PLP_URL')
if PLP_URL:
    PLP_URL = PLP_URL.rstrip('/')

# We should login always with tp-sso
SSO_TP_BACKEND_NAME = 'sso_tp-oauth2'
LOGIN_URL = '/auth/login/%s/' % SSO_TP_BACKEND_NAME

EVMS_URL = ENV_TOKENS.get('EVMS_URL', None)
EVMS_API_KEY = AUTH_TOKENS.get('EVMS_API_KEY', None)

ORA2_FILEUPLOAD_BACKEND = ENV_TOKENS.get('ORA2_FILEUPLOAD_BACKEND', 'filesystem')
ORA2_FILEUPLOAD_ROOT = ENV_TOKENS.get('ORA2_FILEUPLOAD_ROOT', '/edx/var/edxapp/ora2')
ORA2_FILEUPLOAD_CACHE_NAME = ENV_TOKENS.get('ORA2_FILEUPLOAD_CACHE_NAME', 'ora2_cache')

#ROOT_URLCONF = 'sso_edx_tp.lms_urls'

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

FEATURES['ENABLE_GRADE_DOWNLOADS'] = True

TRACK_MAX_EVENT = 327680

if AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT'):
    AWS_S3_CALLING_FORMAT = AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT')

INSTALLED_APPS += (
    # Api extension for eduscaled
    'open_edx_api_extension',
    'video_evms',
    'sso_edx_tp',
)

LOCALE_PATHS = [OPENEDX_ROOT + '/eduscaled/translations'] + LOCALE_PATHS

ORA_PATH_VENV = 'venvs/edxapp/lib/python2.7/site-packages/openassessment'
ORA_LOCALE_PATH = '{}/{}/locale'.format(PROJECT_ROOT.dirname().dirname(), ORA_PATH_VENV)
LOCALE_PATHS.append(ORA_LOCALE_PATH)

ORA_PATH_VENV = 'venvs/edxapp/src/ora2/openassessment'
ORA_LOCALE_PATH = '{}/{}/locale'.format(PROJECT_ROOT.dirname().dirname(), ORA_PATH_VENV)
LOCALE_PATHS.append(ORA_LOCALE_PATH)

PROCTOR_PATH_VENV = 'venvs/edxapp/src/edx-proctoring/edx_proctoring'
PROCTOR_LOCALE_PATH = '{}/{}/locale'.format(PROJECT_ROOT.dirname().dirname(), PROCTOR_PATH_VENV)
LOCALE_PATHS.append(PROCTOR_LOCALE_PATH)


PROCTORING_DEFAULT_LINK_URLS = AUTH_TOKENS.get('PROCTORING_DEFAULT_LINK_URLS')

COURSE_MODE_DEFAULTS = {
    'bulk_sku': None,
    'currency': 'usd',
    'description': None,
    'expiration_datetime': None,
    'min_price': 0,
    'name': _('Honor'),
    'sku': None,
    'slug': 'honor',
    'suggested_prices': '',
}

COPYRIGHT_YEAR = "2018"

FEATURES['ENABLE_SOFTWARE_SECURE_FAKE'] = True

FEATURES["ALLOW_COURSE_STAFF_GRADE_DOWNLOADS"] = True

FEATURES['USE_LANGUAGE_FROM_COURSE_SETTINGS'] = True
FEATURES['ALLOW_HIDING_DISCUSSION_TAB'] = True

CUSTOM_THIRD_PARTY_AUTH_STRATEGY = 'sso_edx_tp.strategy.ConfigurationModelStrategy'
