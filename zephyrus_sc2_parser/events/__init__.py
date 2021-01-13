import logging
from logging import NullHandler
from zephyrus_sc2_parser.events.object_event import ObjectEvent
from zephyrus_sc2_parser.events.ability_event import AbilityEvent
from zephyrus_sc2_parser.events.selection_event import SelectionEvent
from zephyrus_sc2_parser.events.control_group_event import ControlGroupEvent
from zephyrus_sc2_parser.events.upgrade_event import UpgradeEvent
from zephyrus_sc2_parser.events.camera_event import CameraEvent
from zephyrus_sc2_parser.events.player_stats_event import PlayerStatsEvent
from zephyrus_sc2_parser.events.player_leave_event import PlayerLeaveEvent

logging.getLogger(__name__).addHandler(NullHandler())

# to prevent unknown upgrade warnings
upgrade_logger = logging.getLogger(f'{__name__}.upgrade_event')
upgrade_logger.setLevel(logging.ERROR)
