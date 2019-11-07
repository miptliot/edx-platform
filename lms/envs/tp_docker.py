from django.utils.translation import ugettext_lazy as _

from devstack_docker import *


ORA2_FILEUPLOAD_BACKEND = 'filesystem'
USERS_WITH_SPECIAL_PERMS_IDS = []
FEATURES['ENABLE_SPECIAL_EXAMS'] = True

SSO_ENABLED = ENV_TOKENS.get("SSO_ENABLED", True)
PLP_ENABLED = ENV_TOKENS.get("PLP_ENABLED", True)

PLP_URL = ""
SSO_TP_URL = ""

INSTALLED_APPS += (
    # Api extension for eduscaled
    'open_edx_api_extension',
    'sso_edx_tp',
)

THIRD_PARTY_AUTH_BACKENDS = [
    'sso_edx_tp.backends.tp.TpBackend',
    'sso_edx_tp.backends.tp.TpBackendCMS'
]
AUTHENTICATION_BACKENDS = THIRD_PARTY_AUTH_BACKENDS + list(AUTHENTICATION_BACKENDS)

if SSO_ENABLED:
    SSO_TP_URL = ENV_TOKENS.get("SSO_TP_URL", 'http://sso.openedu.test')
    SSO_API_URL = '%s/api-edx/' % SSO_TP_URL
    SSO_API_TOKEN = ENV_TOKENS.get("SSO_API_TOKEN", 'blablabla')
    SSO_PUSH_CHANGES = ENV_TOKENS.get('SSO_PUSH_CHANGES', False)

    SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
    SOCIAL_AUTH_LOGOUT_URL = '%s/logout/' % SSO_TP_URL
    SOCIAL_AUTH_RAISE_EXCEPTIONS = True

    # We should login always with tp-sso
    SSO_TP_BACKEND_NAME = 'sso_tp-oauth2'
    LOGIN_URL = '/auth/login/%s/' % SSO_TP_BACKEND_NAME

    FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
    THIRD_PARTY_AUTH_BACKENDS = [
        'sso_edx_tp.backends.tp.TpBackend',
        'sso_edx_tp.backends.tp.TpBackendCMS'
    ]
    AUTHENTICATION_BACKENDS = THIRD_PARTY_AUTH_BACKENDS + list(AUTHENTICATION_BACKENDS)

    MIDDLEWARE_CLASSES += ('sso_edx_tp.middleware.SeamlessAuthorization',)
    TP_MAKO_TEMPLATES = os.getenv('TP_MAKO_TEMPLATES_LMS',
                                  '/edx/app/edxapp/venvs/edxapp/src/sso-edx-tp/sso_edx_tp/templates/lms')
    TP_MAKO_TEMPLATES = TP_MAKO_TEMPLATES.split(',')
    for T in TEMPLATES:
        if T['NAME'] == 'mako':
            T['DIRS'] = TP_MAKO_TEMPLATES + T['DIRS']
    #ROOT_URLCONF = 'sso_edx_tp.lms_urls'

if SSO_ENABLED and PLP_ENABLED:
    PLP_URL = ENV_TOKENS.get("PLP_URL", 'http://plp.openedu.test')
    PLP_API_KEY = ENV_TOKENS.get("PLP_API_KEY", '123456')
    PLP_BAN_ON = False
    FEATURES['ICALENDAR_DUE_API'] = False
    MIDDLEWARE_CLASSES += ('sso_edx_tp.middleware.PLPRedirection',)

FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = False

EDX_API_KEY = '123456'
# video manager
EVMS_URL = ENV_TOKENS.get('EVMS_URL', None)
EVMS_API_KEY = AUTH_TOKENS.get('EVMS_API_KEY', None)

FEATURES['EVMS_TURN_ON'] = True
if FEATURES['EVMS_TURN_ON']:
    FEATURES['EVMS_QUALITY_CONTROL_ON'] = True
    INSTALLED_APPS += (
        # Api extension for eduscaled
        'video_evms',
    )

PROCTORING_BACKEND_PROVIDERS = {
    "dummy": {
        "class": "edx_proctoring.backends.null.NullBackendProvider",
        "options": {},
        "settings": {}
    },
    "EXAMUS": {
        "class": "examus.backends.examus.ExamusBackendProvider",
        "options": {
            "crypto_key": "123456789012345678901234",
            "exam_register_endpoint": "{add endpoint here}",
            "exam_sponsor": "Examus",
            "organization": "TP",
            "secret_key": "{add SoftwareSecure secret key}",
            "secret_key_id": "{add SoftwareSecure secret key id}",
            "software_download_url": "https://chrome.google.com/webstore/detail/examus/apippgiggejegjpimfjnaigmanampcjg"
        },
        "settings": {
            "LINK_URLS": {
                "contact_us": "{add link here}",
                "faq": "{add link here}",
                "online_proctoring_rules": "{add link here}",
                "tech_requirements": "{add link here}"
            }
        }
    },
    "ITMO": {
        "class": "itmo.backends.itmo.ItmoBackendProvider",
        "options": {
            "crypto_key": "{add key here}",
            "exam_register_endpoint": "{add endpoint here}",
            "exam_sponsor": "ITMO",
            "organization": "org_name",
            "secret_key": "{add key here}",
            "secret_key_id": "{add id here}",
            "software_download_url": "https://de.ifmo.ru:8443/dist/"
        },
        "settings": {
            "LINK_URLS": {
                "contact_us": "{add link here}",
                "faq": "{add link here}",
                "online_proctoring_rules": "{add link here}",
                "tech_requirements": "{add link here}"
            }
        }
    },
    "WEB_ASSISTANT": {
        "class": "tp.backends.assistant.TPBackendProvider",
        "options": {
            "crypto_key": "123456789012345678901234",
            "exam_register_endpoint": "https://proctor.local.se:8002/api/exam_register/",
            "exam_sponsor": "Hobo",
            "organization": "HoboHome",
            "secret_key": "hobo_secret_key!",
            "secret_key_id": "hobo_secret_key_id",
            "software_download_url": "{add link here}"
        },
        "settings": {
            "LINK_URLS": {
                "contact_us": "{add link here}",
                "faq": "{add link here}",
                "online_proctoring_rules": "{add link here}",
                "tech_requirements": "{add link here}"
            }
        }
    }
}
PROCTORING_BACKEND_PROVIDERS = AUTH_TOKENS.get("PROCTORING_BACKEND_PROVIDERS", PROCTORING_BACKEND_PROVIDERS)

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

COPYRIGHT_YEAR = "2019"

FEATURES['ENABLE_SOFTWARE_SECURE_FAKE'] = True
FEATURES['ENABLE_GRADE_DOWNLOADS'] = True
FEATURES["ALLOW_COURSE_STAFF_GRADE_DOWNLOADS"] = True
FEATURES['USE_LANGUAGE_FROM_COURSE_SETTINGS'] = True

LANGUAGE_CODE = 'ru'
DEFAULT_SITE_THEME = 'edx-theme-2035'
ENABLE_COMPREHENSIVE_THEMING = True

PDF_RENDER_BIN = ENV_TOKENS.get('PDF_RENDER_BIN', 'wkhtmltopdf')
