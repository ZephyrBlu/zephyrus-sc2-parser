import pytest
from zephyrus_sc2_parser.game.player import Player
from zephyrus_sc2_parser.events import (
    ObjectEvent, AbilityEvent, SelectionEvent, ControlGroupEvent,
    UpgradeEvent, CameraUpdateEvent, PlayerStatsEvent
)


player_id_assignment_testdata = [
    (
        [Player(0, 0, 1, 1, 'John', 'Zerg'), Player(1, 1, 1, 1, 'Bob', 'Protoss')],
        [Player(1, 0, 1, 1, 'John', 'Zerg'), Player(2, 1, 1, 1, 'Bob', 'Protoss')]
    ),
    (
        [Player(1, 0, 1, 1, 'John', 'Zerg'), Player(2, 1, 1, 1, 'Bob', 'Protoss')],
        [Player(1, 0, 1, 1, 'John', 'Zerg'), Player(2, 1, 1, 1, 'Bob', 'Protoss')]
    ),
    (
        [Player(2, 0, 1, 1, 'John', 'Zerg'), Player(3, 1, 1, 1, 'Bob', 'Protoss')],
        [Player(1, 0, 1, 1, 'John', 'Zerg'), Player(2, 1, 1, 1, 'Bob', 'Protoss')]
    ),
    (
        [Player(0, 0, 1, 1, 'John', 'Zerg')],
        [Player(1, 0, 1, 1, 'John', 'Zerg')]
    ),
    (
        [Player(1, 0, 1, 1, 'John', 'Zerg')],
        [Player(1, 0, 1, 1, 'John', 'Zerg')]
    ),
    (
        [Player(2, 0, 1, 1, 'John', 'Zerg')],
        [Player(1, 0, 1, 1, 'John', 'Zerg')]
    ),
]

@pytest.mark.parametrize("players, expected_players", player_id_assignment_testdata)
def test_create_players_player_id_assignment(players, expected_players):
    if len(players) == 1:
        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = 1
    else:
        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = 1

        player_obj = max(players, key=lambda x: x.player_id)
        player_obj.player_id = 2

    players.sort(key=lambda x: x.player_id)

    for i in range(0, len(players)):
        assert players[i].player_id == expected_players[i].player_id, f"Player {i+1}'s ID was set incorrectly"
        print("Player ID was set correctly")


# mock_event = {'_event': None, '_gameloop': None}
# event_identification_testdata = [
#     ('NNet.Replay.Tracker.SUnitInitEvent', ObjectEvent(None, None, None, mock_event)),
#     ('NNet.Replay.Tracker.SUnitDoneEvent', ObjectEvent(None, None, None, mock_event)),
#     ('NNet.Replay.Tracker.SUnitBornEvent', ObjectEvent(None, None, None, mock_event)),
#     ('NNet.Replay.Tracker.SUnitDiedEvent', ObjectEvent(None, None, None, mock_event)),
#     ('NNet.Replay.Tracker.SUnitTypeChangeEvent', ObjectEvent(None, None, None, mock_event)),
#     ('NNet.Game.SCmdEvent', AbilityEvent(None, None, mock_event)),
#     ('NNet.Game.SCommandManagerStateEvent', AbilityEvent(None, None, mock_event)),
#     ('NNet.Game.SSelectionDeltaEvent', SelectionEvent(None, mock_event)),
#     ('NNet.Game.SControlGroupUpdateEvent', ControlGroupEvent(None, mock_event)),
#     ('NNet.Replay.Tracker.SUpgradeEvent', UpgradeEvent(None, mock_event)),
#     ('NNet.Game.SCameraUpdateEvent', CameraUpdateEvent(None, mock_event)),
#     ('NNet.Replay.Tracker.SPlayerStatsEvent', PlayerStatsEvent(None, None, mock_event)),
#     ('Not a captured event', None),
# ]

# @pytest.mark.parametrize("event_type, expected_event", event_identification_testdata)
# def test_create_event_event_identification(event_type, expected_event):
#     mock_event = {'_event': None, '_gameloop': None}

#     object_events = [
#         'NNet.Replay.Tracker.SUnitInitEvent',
#         'NNet.Replay.Tracker.SUnitDoneEvent',
#         'NNet.Replay.Tracker.SUnitBornEvent',
#         'NNet.Replay.Tracker.SUnitDiedEvent',
#         'NNet.Replay.Tracker.SUnitTypeChangeEvent'
#     ]

#     ability_events = [
#         'NNet.Game.SCmdEvent',
#         'NNet.Game.SCommandManagerStateEvent'
#     ]

#     if event_type in object_events:
#         current_event = ObjectEvent(None, None, None, mock_event)

#     elif event_type in ability_events:
#         current_event = AbilityEvent(None, None, mock_event)

#     elif event_type == 'NNet.Game.SSelectionDeltaEvent':
#         current_event = SelectionEvent(None, mock_event)

#     elif event_type == 'NNet.Game.SControlGroupUpdateEvent':
#         current_event = ControlGroupEvent(None, mock_event)

#     elif event_type == 'NNet.Replay.Tracker.SUpgradeEvent':
#         current_event = UpgradeEvent(None, mock_event)

#     elif event_type == 'NNet.Game.SCameraUpdateEvent':
#         current_event = CameraUpdateEvent(None, mock_event)

#     elif event_type == 'NNet.Replay.Tracker.SPlayerStatsEvent':
#         current_event = PlayerStatsEvent(None, None, mock_event)

#     else:
#         current_event = None

#     assert type(current_event) == type(expected_event), f"Event does not match expected for {event_type} event"

