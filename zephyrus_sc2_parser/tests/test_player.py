import pytest
# from zephyrus_sc2_parser.game.perception_action_cycle import PerceptionActionCycle


calc_pac_testdata = [
    (
        [],
        1,
        {
            'pac_per_min': 0,
            'pac_action_latency': 0,
            'pac_actions': 0,
            'pac_gap': 0,
        },
    ),
]

# is this is integration test not unit test???
@pytest.mark.parametrize("pac_list, game_length, expected_values", calc_pac_testdata)
def test_calc_pac(pac_list, game_length, expected_values):
    game_length_minutes = game_length / 22.4 / 60

    pac_per_min = len(pac_list) / game_length_minutes
    if pac_list:
        avg_pac_action_latency = sum(pac.actions[0] - pac.camera_moves[0][0] for pac in pac_list) / len(pac_list) / 22.4
        avg_actions_per_pac = sum(len(pac.actions) for pac in pac_list) / len(pac_list)
    else:
        avg_pac_action_latency = 0
        avg_actions_per_pac = 0

    pac_gaps = []
    for i in range(0, len(pac_list)-1):
        pac_diff = pac_list[i+1].initial_gameloop - pac_list[i].final_gameloop
        pac_gaps.append(pac_diff)
    if pac_gaps:
        avg_pac_gap = sum(pac_gaps) / len(pac_gaps) / 22.4
    else:
        avg_pac_gap = 0

    assert pac_per_min == expected_values['pac_per_min']
    assert avg_pac_action_latency == expected_values['pac_action_latency']
    assert avg_actions_per_pac == expected_values['pac_actions']
    assert avg_pac_gap == expected_values['pac_gap']
