import logging
from logging import NullHandler
from zephyrus_sc2_parser.parser import parse_replay

logging.getLogger(__name__).addHandler(NullHandler())

# to prevent unknown event warnings
util_logger = logging.getLogger(f'{__name__}.utils')
util_logger.setLevel(logging.ERROR)
