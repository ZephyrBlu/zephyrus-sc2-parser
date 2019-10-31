import pytest
from zephyrus_sc2_parser.game.perception_action_cycle import PerceptionActionCycle


parse_event_testdata = [
    (
        None,
        [],
        {
            '_gameloop': 0,
            'm_target': None,
        },
    ),
    (
        None,
        [],
        {
            '_gameloop': 0,
            'm_target': {'x': 0, 'y': 0},
        },
    ),
    (
        PerceptionActionCycle((0, 0), 0),
        [],
        {
            '_gameloop': 0,
            'm_target': {'x': 0, 'y': 0},
        },
    ),
    (
        PerceptionActionCycle((0, 0), 0),
        [],
        {
            '_gameloop': 5,
            'm_target': {'x': 7, 'y': 0},
        },
    ),
    (
        PerceptionActionCycle((0, 0), 0),
        [],
        {
            '_gameloop': 4,
            'm_target': {'x': 7, 'y': 0},
        },
    ),
]


@pytest.mark.parametrize(
    "player_current_pac, player_pac_list, event",
    parse_event_testdata
)
def test_parse_event(player_current_pac, player_pac_list, event):
    if event['m_target']:
        position = (event['m_target']['x'], event['m_target']['y'])
        gameloop = event['_gameloop']

        if player_current_pac:
            current_pac = player_current_pac
            # If current PAC is still within camera bounds, count action
            if current_pac.check_position(position):
                current_pac.camera_moves.append((gameloop, position))

            # If current PAC is out of camera bounds
            # and meets min duration, save it
            elif current_pac.check_duration(gameloop):
                current_pac.final_camera_position = position
                current_pac.final_gameloop = gameloop

                if current_pac.actions:
                    player_pac_list.append(current_pac)
                player_current_pac = PerceptionActionCycle(position, gameloop)
                player_current_pac.camera_moves.append((gameloop, position))

            # If current PAC is out of camera bounds
            # and does not meet min duration,
            # discard current PAC and create new one
            else:
                player_current_pac = PerceptionActionCycle(position, gameloop)
                player_current_pac.camera_moves.append((gameloop, position))
        else:
            player_current_pac = PerceptionActionCycle(position, gameloop)
            player_current_pac.camera_moves.append((gameloop, position))
