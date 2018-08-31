from devstack import *

ORA2_FILEUPLOAD_BACKEND = 'filesystem'
USERS_WITH_SPECIAL_PERMS_IDS = []
FEATURES['ENABLE_SPECIAL_EXAMS'] = True

SSO_ENABLED = ENV_TOKENS.get("SSO_ENABLED", False)
PLP_ENABLED = ENV_TOKENS.get("PLP_ENABLED", False)

PLP_URL = ""
SSO_NPOED_URL = ""

if SSO_ENABLED:
    SSO_NPOED_URL = ENV_TOKENS.get("SSO_NPOED_URL", 'http://sso.local.se:8080')
    SSO_API_URL = '%s/api-edx/' % SSO_NPOED_URL
    SSO_API_TOKEN = ENV_TOKENS.get("SSO_API_TOKEN", '123456')

    SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
    SOCIAL_AUTH_LOGOUT_URL = '%s/logout/' % SSO_NPOED_URL
    SOCIAL_AUTH_RAISE_EXCEPTIONS = True

    # We should login always with npoed-sso
    SSO_NPOED_BACKEND_NAME = 'sso_npoed-oauth2'
    LOGIN_URL = '/auth/login/%s/' % SSO_NPOED_BACKEND_NAME

    FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
    THIRD_PARTY_AUTH_BACKENDS = [
        'sso_edx_npoed.backends.npoed.NpoedBackend',
        'sso_edx_npoed.backends.npoed.NpoedBackendCMS'
    ]
    AUTHENTICATION_BACKENDS = THIRD_PARTY_AUTH_BACKENDS + list(AUTHENTICATION_BACKENDS)

    MIDDLEWARE_CLASSES += ('sso_edx_npoed.middleware.SeamlessAuthorization',)

    ROOT_URLCONF = 'sso_edx_npoed.lms_urls'

if SSO_ENABLED and PLP_ENABLED:
    PLP_URL = ENV_TOKENS.get("PLP_URL", 'http://plp.local.se:8081')
    PLP_API_KEY = ENV_TOKENS.get("PLP_API_KEY", '123456')
    PLP_BAN_ON = True
    FEATURES['ICALENDAR_DUE_API'] = True
    MIDDLEWARE_CLASSES += ('sso_edx_npoed.middleware.PLPRedirection',)

FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = True

NPOED_MAKO_TEMPLATES = ["/edx/app/edxapp/venvs/edxapp/src/sso-edx-npoed/sso_edx_npoed/templates/lms", ]

# video manager
EVMS_URL = 'https://evms.test.npoed.ru'
EVMS_API_KEY = 'xxxxxxxxxxxxxxxxxx'

INSTALLED_APPS += (
    # Api extension for openedu
    'open_edx_api_extension',
    'video_evms',
    'rg_instructor_analytics',
)

FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT'] = True
FEATURES['ENABLE_RG_INSTRUCTOR_ANALYTICS'] = True

RG_ANALYTICS_ENROLLMENT_STAT_UPDATE = {
    'minute': '*',
    'hour': '*/6',
    'day_of_week': '*',
    'day_of_month': '*',
    'month_of_year': '*',
}

RG_ANALYTICS_GRADE_STAT_UPDATE = {
    'minute': '*',
    'hour': '*/6',
    'day_of_week': '*',
    'day_of_month': '*',
    'month_of_year': '*',
}
