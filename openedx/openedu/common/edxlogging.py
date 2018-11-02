import sys
import logging
from logging.handlers import SysLogHandler


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
                              syslog_address=('127.0.0.1', 514, ),
                              service_variant="",
                              use_raven=False, use_stsos=False):

    format_notime = ("{service_variant}|%(name)s|%(levelname)s"
                     "|%(process)d|%(filename)s:%(lineno)d"
                     " %(message)s").format(service_variant=service_variant)
    format_withtime = "%(asctime)s {}".format(format_notime)
    format_console = ('format_withtme' if sys.stdout.isatty() else
                      'format_notime')

    logger_config['filters']['filter_tracking'] = {
        '()': 'openedx.openedu.common.edxlogging.FilterTracking',
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
                '()': 'openedx.core.lib.stsos_logging.StsosFilter',
            }
        })
        logger_config['handlers'].update({
            'stsos': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'facility': SysLogHandler.LOG_LOCAL2,
                'formatter': 'raw',
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
            logger_config['handlers'][item].update({
                'address': syslog_address,
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
                    if item in logger_config['loggers'][logger]['handlers']:
                        logger_config['loggers'][logger]['handlers'].append(
                            handler_file
                        )

    return logger_config
