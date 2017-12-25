# -*- coding: utf-8 -*-

import os

_dir = os.path.dirname(__file__)
_file = os.path.join(os.path.dirname(_dir), 'completor.log')


_log_filter = {}


_conf = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s][%(pathname)s] %(message)s'
        }
    },
    'filters': {
        'default': _log_filter,
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': _file,
            'delay': 1,
            'formatter': 'default'
        }
    },
    'loggers': {
        'completor': {
            'level': 'INFO',
            'handlers': ['file'],
            'filters': ['default'],
            'propagate': False,
        }
    }
}


def config_logging(f):
    import logging.config
    _log_filter['()'] = f
    logging.config.dictConfig(_conf)
