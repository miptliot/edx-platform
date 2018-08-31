import datetime
from devstack import *

FEATURES['ENABLE_SPECIAL_EXAMS'] = True

SSO_ENABLED = ENV_TOKENS.get("SSO_ENABLED", False)

SSO_NPOED_URL = ""

if SSO_ENABLED:
    SSO_NPOED_URL = ENV_TOKENS.get("SSO_NPOED_URL", 'http://sso.local.se:8080')
    SSO_API_URL = '%s/api-edx/' % SSO_NPOED_URL
    SSO_API_TOKEN = ENV_TOKENS.get("SSO_API_TOKEN", '123456')

    SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
    SOCIAL_AUTH_LOGOUT_URL = '%s/logout/' % SSO_NPOED_URL
    SOCIAL_AUTH_RAISE_EXCEPTIONS = True
    # We should login always with npoed-sso. There is specific backend for cms
    # from sso_edx_npoed.backends.npoed import NpoedBackendCMS
    # NpoedBackendCMS.name
    SSO_NPOED_BACKEND_NAME = 'sso_npoed_cms-oauth2'
    LOGIN_URL = '/auth/login/%s/' % SSO_NPOED_BACKEND_NAME

    MIDDLEWARE_CLASSES += ('sso_edx_npoed.middleware.SeamlessAuthorization',)

    ROOT_URLCONF = 'sso_edx_npoed.cms_urls'

    CELERYBEAT_SCHEDULE = {}

    FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
    THIRD_PARTY_AUTH_BACKENDS = [
        'sso_edx_npoed.backends.npoed.NpoedBackend',
        'sso_edx_npoed.backends.npoed.NpoedBackendCMS'
    ]
    AUTHENTICATION_BACKENDS = THIRD_PARTY_AUTH_BACKENDS + list(AUTHENTICATION_BACKENDS)

    SOCIAL_AUTH_PIPELINE_TIMEOUT = 30

    # third_party_auth config moved to ConfigurationModels. This is for data migration only:
    THIRD_PARTY_AUTH_OLD_CONFIG = AUTH_TOKENS.get('THIRD_PARTY_AUTH', None)

    THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS = 24
    CELERYBEAT_SCHEDULE['refresh-saml-metadata'] = {
        'task': 'third_party_auth.fetch_saml_metadata',
        'schedule': datetime.timedelta(hours=24),
    }

    # Add extra dir for mako templates finder
    NPOED_MAKO_TEMPLATES = ["/edx/app/edxapp/venvs/edxapp/src/sso-edx-npoed/sso_edx_npoed/templates/cms", ]

    MAKO_TEMPLATES['main'] = NPOED_MAKO_TEMPLATES + MAKO_TEMPLATES['main']

# video manager
EVMS_URL = 'https://evms.test.npoed.ru'
EVMS_API_KEY = 'xxxxxxxxxxxxxxxxxx'

FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = True

EDX_API_KEY = AUTH_TOKENS.get("EDX_API_KEY")
INSTALLED_APPS += (
    # Api extension for openedu
    'video_evms',
    'open_edx_api_extension_cms',
)

FEATURES['EVMS_TURN_ON'] = True
FEATURES["EVMS_QUALITY_CONTROL_ON"] = True
