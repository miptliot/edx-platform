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

SSO_TP_URL = ENV_TOKENS.get('SSO_TP_URL', 'http://sso.local.se:8081').rstrip('/')

SSO_API_URL = '%s/api-edx/' % SSO_TP_URL
SSO_API_TOKEN = AUTH_TOKENS.get('SSO_API_TOKEN')

# for the branch hawthorn_saas_docker must be True by default
SSO_PUSH_CHANGES = ENV_TOKENS.get('SSO_PUSH_CHANGES', True)

SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
SOCIAL_AUTH_LOGOUT_URL = '%s/logout/' % SSO_TP_URL
SOCIAL_AUTH_RAISE_EXCEPTIONS = True

MIDDLEWARE_CLASSES += (
    'sso_edx_tp.middleware.SeamlessAuthorization',
)

SSO_TP_BACKEND_NAME = 'sso_tp_cms-oauth2'
LOGIN_URL = '/auth/login/%s/' % SSO_TP_BACKEND_NAME

PLP_URL = ENV_TOKENS.get('PLP_URL', 'http://plp.local.se:8080').rstrip('/')

# Copy-paste base third party auth settings from lms
##### Third-party auth options ################################################
if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    AUTHENTICATION_BACKENDS = (
        ENV_TOKENS.get('THIRD_PARTY_AUTH_BACKENDS', []) + list(AUTHENTICATION_BACKENDS)
    )

    # The reduced session expiry time during the third party login pipeline. (Value in seconds)
    SOCIAL_AUTH_PIPELINE_TIMEOUT = ENV_TOKENS.get('SOCIAL_AUTH_PIPELINE_TIMEOUT', 600)
    SOCIAL_AUTH_OAUTH_SECRETS = AUTH_TOKENS.get('SOCIAL_AUTH_OAUTH_SECRETS', {})

# Only staff users will have ability to crate course
FEATURES['DISABLE_COURSE_CREATION'] = True


PROCTORING_BACKEND_PROVIDERS = {
    'default': {
        'class': 'edx_proctoring.backends.null.NullBackendProvider',
        'options': {},
    }
}
PROCTORING_BACKEND_PROVIDERS = AUTH_TOKENS.get("PROCTORING_BACKEND_PROVIDERS", PROCTORING_BACKEND_PROVIDERS)
FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = FEATURES.get('PROCTORED_EXAMS_ATTEMPT_DELETE', False)

EDX_API_KEY = AUTH_TOKENS.get("EDX_API_KEY")

FILE_UPLOAD_STORAGE_BUCKET_NAME = ENV_TOKENS.get('FILE_UPLOAD_STORAGE_BUCKET_NAME', None)

XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds

if AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT'):
    AWS_S3_CALLING_FORMAT = AUTH_TOKENS.get('AWS_S3_CALLING_FORMAT')

AWS_STORAGE_BUCKET_NAME = AUTH_TOKENS.get('AWS_STORAGE_BUCKET_NAME', 'edxuploads')


FEATURES['EVMS_TURN_ON'] = False

if FEATURES['EVMS_TURN_ON']:
    INSTALLED_APPS += (
        # Api extension for eduscaled
        'video_evms',
    )
    FEATURES['EVMS_QUALITY_CONTROL_ON'] = True
    EVMS_URL = ENV_TOKENS.get('EVMS_URL', None)
    EVMS_API_KEY = AUTH_TOKENS.get('EVMS_API_KEY', None)

LOCALE_PATHS = [REPO_ROOT + "/eduscaled/tp_translations"] + LOCALE_PATHS

COMMENTS_SERVICE_URL = ENV_TOKENS.get('COMMENTS_SERVICE_URL', '')
COMMENTS_SERVICE_KEY = ENV_TOKENS.get('COMMENTS_SERVICE_KEY', '')

COPYRIGHT_YEAR = "2018"

FEATURES['ENABLE_CMS_API'] = True
if FEATURES['ENABLE_CMS_API']:
    INSTALLED_APPS += (
        'open_edx_api_extension_cms',
    )

CUSTOM_THIRD_PARTY_AUTH_STRATEGY = 'sso_edx_tp.strategy.ConfigurationModelStrategy'

INSTALLED_APPS += (
    'sso_edx_tp',
)
