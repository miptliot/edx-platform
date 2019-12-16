from devstack import *

SSO_ENABLED = ENV_TOKENS.get('SSO_ENABLED', False)

SSO_TP_URL = ''

if SSO_ENABLED:
    SSO_TP_URL = ENV_TOKENS.get('SSO_TP_URL', 'http://sso.local.se:8081')
    SSO_API_URL = '%s/api-edx/' % SSO_TP_URL
    SSO_API_TOKEN = ENV_TOKENS.get('SSO_API_TOKEN', '123456')
    SSO_PUSH_CHANGES = ENV_TOKENS.get('SSO_PUSH_CHANGES', False)

    SOCIAL_AUTH_EXCLUDE_URL_PATTERN = r'^/admin'
    SOCIAL_AUTH_LOGOUT_URL = '%s/logout/' % SSO_TP_URL
    SOCIAL_AUTH_RAISE_EXCEPTIONS = True
    # We should login always with tp-sso. There is specific backend for cms
    # from sso_edx_tp.backends.tp import TpBackendCMS
    # TpBackendCMS.name
    SSO_TP_BACKEND_NAME = 'sso_tp_cms-oauth2'
    LOGIN_URL = '/auth/login/%s/' % SSO_TP_BACKEND_NAME

    MIDDLEWARE_CLASSES += ('sso_edx_tp.middleware.SeamlessAuthorization',)

    ROOT_URLCONF = 'sso_edx_tp.cms_urls'

    FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True
    THIRD_PARTY_AUTH_BACKENDS = [
        'sso_edx_tp.backends.tp.TpBackend',
        'sso_edx_tp.backends.tp.TpBackendCMS',
    ]
    AUTHENTICATION_BACKENDS = THIRD_PARTY_AUTH_BACKENDS + list(AUTHENTICATION_BACKENDS)

    SOCIAL_AUTH_PIPELINE_TIMEOUT = 30

    # Add extra dir for mako templates finder
    TP_MAKO_TEMPLATES = ['/edx/app/edxapp/venvs/edxapp/src/sso-edx-tp/sso_edx_tp/templates/cms', ]

    MAKO_TEMPLATES['main'] = TP_MAKO_TEMPLATES + MAKO_TEMPLATES['main']

# video manager
EVMS_URL = ENV_TOKENS.get('EVMS_URL', None)
EVMS_API_KEY = AUTH_TOKENS.get('EVMS_API_KEY', None)

EDX_API_KEY = AUTH_TOKENS.get("EDX_API_KEY")

RALL_URL = ENV_TOKENS.get('RALL_URL', 'http://localhost')
RALL_PLATFORM_ID = ENV_TOKENS.get('RALL_PLATFORM_ID', None)
RALL_API_TOKEN = AUTH_TOKENS.get('RALL_API_TOKEN', None)

FEATURES['PROCTORED_EXAMS_ATTEMPT_DELETE'] = True

FEATURES['EVMS_TURN_ON'] = True
if FEATURES['EVMS_TURN_ON']:
    FEATURES['EVMS_QUALITY_CONTROL_ON'] = True
    INSTALLED_APPS += (
        # Api extension for eduscaled
        'video_evms',
    )

FEATURES['ENABLE_SPECIAL_EXAMS'] = True

FEATURES['ENABLE_CMS_API'] = True
if FEATURES['ENABLE_CMS_API']:
    INSTALLED_APPS += (
        'open_edx_api_extension_cms',
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

COPYRIGHT_YEAR = "2018"

LANGUAGE_CODE = 'ru'
