import os
import json
from .common import *

# due to a bug in simple_history
DATABASES = {
    "default": {
        "ENGINE": "",
    }
}

CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""
with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

STATIC_URL_BASE = ENV_TOKENS.get('STATIC_URL_BASE')
if not STATIC_URL_BASE.endswith('/'):
    STATIC_URL_BASE += '/'
STATIC_URL = STATIC_URL_BASE.encode('ascii') + EDX_PLATFORM_REVISION + '/'

STATIC_ROOT = path(ENV_TOKENS.get('STATIC_ROOT_BASE')) / EDX_PLATFORM_REVISION

for app in ENV_TOKENS.get('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS += (app, )
# FIXME: repeated from npoed.py
INSTALLED_APPS += (
    'open_edx_api_extension_cms',
    'video_evms',
)

COMPREHENSIVE_THEME_DIRS = ENV_TOKENS.get('COMPREHENSIVE_THEME_DIRS', COMPREHENSIVE_THEME_DIRS) or []
