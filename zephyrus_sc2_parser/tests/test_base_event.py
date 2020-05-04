import pytest
from zephyrus_sc2_parser.game.player import Player


player1 = Player(1, None, None, None, 'Bob', 'Zerg')
player2 = Player(2, None, None, None, 'John', 'Protoss')

player1.user_id = 1
player2.user_id = 2

identify_player_testdata = [
    (
        {
            '_event': None,
        },
        [],
        None,
    ),
    (
        {
            '_event': 'NNet.Replay.Tracker.SUnitDoneEvent',
        },
        [],
        False,
    ),
    (
        {
            '_event': 'NNet.Replay.Tracker.SUnitDiedEvent',
        },
        [],
        False,
    ),
    (
        {
            '_event': 'NNet.Replay.Tracker.SUnitTypeChangeEvent',
        },
        [],
        False,
    ),
    (
        {
            '_event': '<any other captured event>',
        },
        [player1, player2],
        None,
    ),
    (
        {
            '_event': '<any other captured event>',
            'm_controlPlayerId': 1,
        },
        [player1, player2],
        player1,
    ),
    (
        {
            '_event': '<any other captured event>',
            'm_playerId': 1,
        },
        [player1, player2],
        player1,
    ),
    (
        {
            '_event': '<any other captured event>',
            '_userid': {'m_userId': 1},
        },
        [player1, player2],
        player1,
    ),
    (
        {
            '_event': '<any other captured event>',
            'm_controlPlayerId': 2,
        },
        [player1, player2],
        player2,
    ),
    (
        {
            '_event': '<any other captured event>',
            'm_playerId': 2,
        },
        [player1, player2],
        player2,
    ),
    (
        {
            '_event': '<any other captured event>',
            '_userid': {'m_userId': 2},
        },
        [player1, player2],
        player2,
    ),
]


@pytest.mark.parametrize(
    "event, players, expected_response",
    identify_player_testdata
)
def test_identify_player(event, players, expected_response):
    no_player = [
        'NNet.Replay.Tracker.SUnitDoneEvent',
        'NNet.Replay.Tracker.SUnitDiedEvent',
        'NNet.Replay.Tracker.SUnitTypeChangeEvent'
    ]

    if event['_event'] in no_player:
        assert expected_response is False

    for p in players:
        if 'm_controlPlayerId' in event:
            if p.player_id == event['m_controlPlayerId']:
                assert p == expected_response
        elif 'm_playerId' in event:
            if p.player_id == event['m_playerId']:
                assert p == expected_response
        elif '_userid' in event:
            if p.user_id == event['_userid']['m_userId']:
                assert p == expected_response
        else:
            assert expected_response is None
