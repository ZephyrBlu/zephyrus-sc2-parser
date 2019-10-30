import pytest


parse_event_testdata = [
    (
        1,
        None,
        {},
        None,
        None,
        {'inject_count': {1: 0, 2: 0}},
    ),
    (
        2,
        None,
        {},
        None,
        None,
        {'inject_count': {1: 0, 2: 0}},
    ),
    (
        1,
        None,
        {'m_abil': None},
        'NNet.Game.SCmdEvent',
        None,
        {'inject_count': {1: 0, 2: 0}},
    ),
    (
        2,
        None,
        {'m_abil': None},
        'NNet.Game.SCmdEvent',
        None,
        {'inject_count': {1: 0, 2: 0}},
    ),
    (
        1,
        None,
        {'m_abil': {'m_abilLink': 100, 'm_abilCmdIndex': 0}},
        'NNet.Game.SCmdEvent',
        (100, 0),
        {'inject_count': {1: 0, 2: 0}},
    ),
    (
        2,
        None,
        {'m_abil': {'m_abilLink': 100, 'm_abilCmdIndex': 0}},
        'NNet.Game.SCmdEvent',
        (100, 0),
        {'inject_count': {1: 0, 2: 0}},
    ),
    (
        1,
        None,
        {'m_abil': {'m_abilLink': 183, 'm_abilCmdIndex': 0}},
        'NNet.Game.SCmdEvent',
        (183, 0),
        {'inject_count': {1: 1, 2: 0}},
    ),
    (
        2,
        None,
        {'m_abil': {'m_abilLink': 183, 'm_abilCmdIndex': 0}},
        'NNet.Game.SCmdEvent',
        (183, 0),
        {'inject_count': {1: 0, 2: 1}},
    ),
    (
        1,
        (183, 0),
        {},
        None,
        (183, 0),
        {'inject_count': {1: 1, 2: 0}},
    ),
    (
        2,
        (183, 0),
        {},
        None,
        (183, 0),
        {'inject_count': {1: 0, 2: 1}},
    ),
]


@pytest.mark.parametrize(
    "player_id, active_ability, event, event_type, expected_active_ability, expected_summary_stats",
    parse_event_testdata
)
def test_parse_event(
    player_id,
    active_ability,
    event,
    event_type,
    expected_active_ability,
    expected_summary_stats
):
    summary_stats = {'inject_count': {1: 0, 2: 0}}

    if event_type == 'NNet.Game.SCmdEvent':
        if event['m_abil']:
            if event['m_abil']['m_abilLink'] and type(event['m_abil']['m_abilCmdIndex']) is int:
                ability = (
                    event['m_abil']['m_abilLink'],
                    event['m_abil']['m_abilCmdIndex']
                )
            else:
                ability = None
            new_active_ability = ability

            assert new_active_ability == expected_active_ability

            if new_active_ability and new_active_ability[0] == 183:
                summary_stats['inject_count'][player_id] += 1
    else:
        if active_ability and active_ability[0] == 183:
            summary_stats['inject_count'][player_id] += 1

    assert summary_stats == expected_summary_stats
