import logging
from logging import NullHandler
from .object_event import ObjectEvent
from .ability_event import AbilityEvent
from .selection_event import SelectionEvent
from .control_group_event import ControlGroupEvent
from .upgrade_event import UpgradeEvent
from .camera_update_event import CameraUpdateEvent
from .player_stats_event import PlayerStatsEvent
from .player_leave_event import PlayerLeaveEvent

logging.getLogger(__name__).addHandler(NullHandler())

__all__ = [
    "ObjectEvent",
    "AbilityEvent",
    "SelectionEvent",
    "ControlGroupEvent",
    "UpgradeEvent",
    "CameraUpdateEvent",
    "PlayerStatsEvent",
    "PlayerLeaveEvent",
]
