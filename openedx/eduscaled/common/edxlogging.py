import socket
import sys
import logging
from logging.handlers import SysLogHandler, SYSLOG_UDP_PORT


class FilterTracking(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            l = len(record.msg)
        elif isinstance(record.msg, unicode):  # noqa: F821
            l = len(record.msg.encode('utf-8'))
        else:
            # unlikely
            raise(RuntimeError, "unknown type {}".format(type(record.msg)))

        # UDP max size (65536) minus prefix of a reasonable length
        if l >= 65200:
            return False

        if record.msg.startswith('{"username": "",'):
            return False

        return True


def get_patched_logger_config(logger_config, log_dir=None,
                              service_variant="",
                              use_raven=False, use_stsos=False, log_settings=None):

    if not log_settings:
        log_settings = {}
    syslog_use_tcp = log_settings.get('syslog_use_tcp')
    syslog_host = log_settings.get('syslog_host')
    syslog_port = log_settings.get('syslog_port')
    syslog_port = syslog_port if syslog_port > 0 else SYSLOG_UDP_PORT
    syslog_socket_timeout = log_settings.get('syslog_socket_timeout')

    format_notime = ("{service_variant}|%(name)s|%(levelname)s"
                     "|%(process)d|%(filename)s:%(lineno)d"
                     " %(message)s").format(service_variant=service_variant)
    format_withtime = "%(asctime)s {}".format(format_notime)
    format_console = ('format_withtime' if sys.stdout.isatty() else
                      'format_notime')

    logger_config['filters']['filter_tracking'] = {
        '()': 'openedx.eduscaled.common.edxlogging.FilterTracking',
    }

    logger_config['formatters'].update({
        'format_notime': {
            'format': format_notime,
        },
        'format_withtime': {
            'format': format_withtime,
        },
    })

    logger_config['handlers']['local']['formatter'] = format_console
    logger_config['handlers']['console']['formatter'] = format_console

    if use_raven:
        logger_config['handlers'].update({
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',  # noqa: E501
            }
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

    if use_stsos:
        logger_config['filters'].update({
            'stsos': {
                '()': 'openedx.eduscaled.lms.stsos.logfilter.StsosFilter',
            }
        })
        logger_config['handlers'].update({
            'stsos': {
                'level': 'INFO',
                'class': 'openedx.core.lib.logsettings.ExtendedSysLogHandler',
                'address': (syslog_host, syslog_port) if syslog_host else '/dev/log',
                'facility': SysLogHandler.LOG_LOCAL2,
                'formatter': 'raw',
                'socktype': socket.SOCK_STREAM if syslog_use_tcp else socket.SOCK_DGRAM,
                'socktimeout': syslog_socket_timeout,
                'filters': ['stsos'],
            }
        })
        logger_config['loggers'].update({
            'stsos': {
                'level': 'INFO',
                'handlers': ['stsos'],
                'propagate': False,
            },
        })

    for item in ['tracking', 'local', 'stsos']:
        if item in logger_config['handlers']:
            if logger_config['handlers'][item].get('address') == '/dev/log' and syslog_host:
                logger_config['handlers'][item].update({
                    'address': (syslog_host, syslog_port),
                })

            if log_dir:
                handler_file = '{}_file'.format(item)
                logger_config['handlers'].update({
                    handler_file: {
                        'class': 'logging.handlers.RotatingFileHandler',
                        'filename': '{}/{}.log'.format(log_dir, item),
                        'maxBytes': 1024*1024*10,
                        'backupCount': 9,
                    }
                })
                if 'filters' in logger_config['handlers'][item]:
                    logger_config['handlers'][handler_file].update({
                        'filters': logger_config['handlers'][item]['filters'],
                    })
                for logger in logger_config['loggers']:
                    if 'handlers' in logger_config['loggers'][logger] and item in logger_config['loggers'][logger]['handlers']:
                        logger_config['loggers'][logger]['handlers'].append(
                            handler_file
                        )

    return logger_config
