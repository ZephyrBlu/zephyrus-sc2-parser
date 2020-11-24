import logging
from logging import NullHandler
from zephyrus_sc2_parser.parser import parse_replay

logging.getLogger(__name__).addHandler(NullHandler())
