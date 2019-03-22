from django.utils.translation import ugettext_lazy as _

from devstack import *

ORA2_FILEUPLOAD_BACKEND = 'filesystem'
USERS_WITH_SPECIAL_PERMS_IDS = []
FEATURES['ENABLE_SPECIAL_EXAMS'] = True

SSO_ENABLED = ENV_TOKENS.get("SSO_ENABLED", True)
PLP_ENABLED = ENV_TOKENS.get("PLP_ENABLED", False)

PLP_URL = ""
SSO_TP_URL = ""

if SSO_ENABLED:
    SSO_TP_URL = ENV_TOKENS.get("SSO_TP_URL", 'http://sso.local.se:8081')
    SSO_API_URL = '%s/api-edx/' % SSO_TP_URL
    SSO_API_TOKEN = ENV_TOKENS.get("SSO_API_TOKEN", '123456')

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

    ROOT_URLCONF = 'sso_edx_tp.lms_urls'

if SSO_ENABLED and PLP_ENABLED:
    PLP_URL = ENV_TOKENS.get("PLP_URL", 'http://plp.local.se:8080')
    PLP_API_KEY = ENV_TOKENS.get("PLP_API_KEY", '123456')
    PLP_BAN_ON = True
    FEATURES['ICALENDAR_DUE_API'] = True
    MIDDLEWARE_CLASSES += ('sso_edx_tp.middleware.PLPRedirection',)

FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = True

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

EXAMUS_INVOLVEMENT_ENABLED = ENV_TOKENS.get('EXAMUS_INVOLVEMENT_ENABLED', False)
EXAMUS_INVOLVEMENT_TOKEN_NAME = AUTH_TOKENS.get('EXAMUS_INVOLVEMENT_TOKEN_NAME', 'replace-me')
EXAMUS_INVOLVEMENT_TOKEN_SECRET = AUTH_TOKENS.get('EXAMUS_INVOLVEMENT_TOKEN_SECRET', 'replace-me')
EXAMUS_INVOLVEMENT_API_HOST = AUTH_TOKENS.get('EXAMUS_INVOLVEMENT_API_HOST', 'https://faceNLZ.dev.examus.net')
EXAMUS_INVOLVEMENT_CHARTS_HOST = AUTH_TOKENS.get('EXAMUS_INVOLVEMENT_CHARTS_HOST', 'https://cdn.facenlz.examus.net')

INSTALLED_APPS += (
    # Api extension for eduscaled
    'open_edx_api_extension',
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
