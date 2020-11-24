import logging

default_logging = {
    'handlers': {
        'console': {
            'class': logging.StreamHandler,
            'level': logging.WARNING,
        },
        'file': {
            'class': logging.FileHandler,
            'level': logging.WARNING,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': logging.WARNING,
    },
}
