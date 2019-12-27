"""Get log settings."""

import logging
import socket
import platform
import sys
import warnings
from logging.handlers import SysLogHandler, SYSLOG_UDP_PORT

LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class ExtendedSysLogHandler(logging.handlers.SysLogHandler):

    def __init__(self, address=('localhost', SYSLOG_UDP_PORT),
                 facility=logging.handlers.SysLogHandler.LOG_USER,
                 socktype=None,
                 socktimeout=0):
        self.socktimeout = socktimeout
        super(ExtendedSysLogHandler, self).__init__(address=address, facility=facility, socktype=socktype)
        if self.socktimeout > 0:
            self.socket.settimeout(self.socktimeout)


def get_logger_config(log_dir,
                      logging_env="no_env",
                      local_loglevel='INFO',
                      service_variant="",
                      log_settings=None,
                      raven_dsn=None):

    """

    Return the appropriate logging config dictionary. You should assign the
    result of this to the LOGGING var in your settings. The reason it's done
    this way instead of registering directly is because I didn't want to worry
    about resetting the logging state if this is called multiple times when
    settings are extended.
    """

    # Revert to INFO if an invalid string is passed in
    if local_loglevel not in LOG_LEVELS:
        local_loglevel = 'INFO'

    hostname = platform.node().split(".")[0]
    syslog_format = ("[service_variant={service_variant}]"
                     "[%(name)s][env:{logging_env}] %(levelname)s "
                     "[{hostname}  %(process)d] [%(filename)s:%(lineno)d] "
                     "- %(message)s").format(service_variant=service_variant,
                                             logging_env=logging_env,
                                             hostname=hostname)

    if not log_settings:
        log_settings = {}
    syslog_use_tcp = log_settings.get('syslog_use_tcp')
    syslog_host = log_settings.get('syslog_host')
    syslog_port = log_settings.get('syslog_port')
    syslog_port = syslog_port if syslog_port > 0 else SYSLOG_UDP_PORT
    syslog_socket_timeout = log_settings.get('syslog_socket_timeout')

    logger_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s %(levelname)s %(process)d '
                          '[%(name)s] %(filename)s:%(lineno)d - %(message)s',
            },
            'syslog_format': {'format': syslog_format},
            'raw': {'format': '%(message)s'},
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stderr,
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            },
            'local': {
                'level': local_loglevel,
                'class': 'openedx.core.lib.logsettings.ExtendedSysLogHandler',
                'address': (syslog_host, syslog_port) if syslog_host else '/dev/log',
                'formatter': 'syslog_format',
                'facility': SysLogHandler.LOG_LOCAL0,
                'socktype': socket.SOCK_STREAM if syslog_use_tcp else socket.SOCK_DGRAM,
                'socktimeout': syslog_socket_timeout
            },
            'tracking': {
                'level': 'DEBUG',
                'class': 'openedx.core.lib.logsettings.ExtendedSysLogHandler',
                'address': (syslog_host, syslog_port) if syslog_host else '/dev/log',
                'facility': SysLogHandler.LOG_LOCAL1,
                'formatter': 'raw',
                'socktype': socket.SOCK_STREAM if syslog_use_tcp else socket.SOCK_DGRAM,
                'socktimeout': syslog_socket_timeout
            },
        },
        'loggers': {
            'tracking': {
                'handlers': ['tracking'],
                'level': 'DEBUG',
                'propagate': False,
            },
            '': {
                'handlers': ['console', 'local'],
                'level': 'INFO',
                'propagate': False
            },
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
            },
            # requests is so loud at INFO (logs every connection) that we
            # force it to warn by default.
            'requests.packages.urllib3': {
                'level': 'WARN'
            }
        }
    }

    if raven_dsn:
        logger_config['handlers'].update({
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            },
        })
        logger_config['loggers'].update({
            'raven': {
                'level': 'DEBUG',
                'handlers': ['console', 'sentry'],
                'propagate': False,
            },
            'sentry.errors': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
        })

    return logger_config


def log_python_warnings():
    """
    Stop ignoring DeprecationWarning, ImportWarning, and PendingDeprecationWarning;
    log all Python warnings to the main log file.

    Not used in test runs, so pytest can collect the warnings triggered for
    each test case.
    """
    warnings.simplefilter('default')
    warnings.filterwarnings('ignore', 'Not importing directory ')
    warnings.filterwarnings('ignore', 'Setting _field_data is deprecated')
    warnings.filterwarnings('ignore', 'Setting _field_data via the constructor is deprecated')
    try:
        # There are far too many of these deprecation warnings in startup to output for every management command;
        # suppress them until we've fixed at least the most common ones as reported by the test suite
        from django.utils.deprecation import RemovedInDjango20Warning, RemovedInDjango21Warning
        warnings.simplefilter('ignore', RemovedInDjango20Warning)
        warnings.simplefilter('ignore', RemovedInDjango21Warning)
    except ImportError:
        pass
    logging.captureWarnings(True)
