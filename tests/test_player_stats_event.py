import pytest
from zephyrus_sc2_parser.game.player import Player


mock_player1 = Player(1, None, None, None, None, None)
unspent_and_collection_testdata = [
    (
        mock_player1,
        {
            '_event': 'NNet.Replay.Tracker.SPlayerStatsEvent',
            '_gameloop': 1,
            'm_stats': {
                'm_scoreValueMineralsCurrent': 0,
                'm_scoreValueVespeneCurrent': 0,
                'm_scoreValueMineralsCollectionRate': 0,
                'm_scoreValueVespeneCollectionRate': 0,
                'm_scoreValueMineralsLostArmy': 0,
                'm_scoreValueVespeneLostArmy': 0,
                'm_scoreValueWorkersActiveCount': 12,
            },
        },
        {'gas': [], 'minerals': []},
        {'gas': [], 'minerals': []},
    ),
    (
        mock_player1,
        {
            '_event': 'NNet.Replay.Tracker.SPlayerStatsEvent',
            '_gameloop': 2,
            'm_stats': {
                'm_scoreValueMineralsCurrent': 0,
                'm_scoreValueVespeneCurrent': 0,
                'm_scoreValueMineralsCollectionRate': 0,
                'm_scoreValueVespeneCollectionRate': 0,
                'm_scoreValueMineralsLostArmy': 0,
                'm_scoreValueVespeneLostArmy': 0,
                'm_scoreValueWorkersActiveCount': 12,
            },
        },
        {'gas': [0], 'minerals': [0]},
        {'gas': [0], 'minerals': [0]},
    ),
]


@pytest.mark.parametrize(
    "player, event, expected_unspent_resources, expected_collection_rate",
    unspent_and_collection_testdata,
)
def test_parse_event_unspent_resources_and_collection_rate(
    player,
    event,
    expected_unspent_resources,
    expected_collection_rate,
):
    gameloop = event['_gameloop']
    unspent_resources = player.unspent_resources
    collection_rate = player.collection_rate

    if gameloop != 1:
        unspent_resources['minerals'].append(
            event['m_stats']['m_scoreValueMineralsCurrent']
        )
        unspent_resources['gas'].append(
            event['m_stats']['m_scoreValueVespeneCurrent']
        )

        collection_rate['minerals'].append(
            event['m_stats']['m_scoreValueMineralsCollectionRate']
        )
        collection_rate['gas'].append(
            event['m_stats']['m_scoreValueVespeneCollectionRate']
        )

    assert unspent_resources == expected_unspent_resources
    assert collection_rate == expected_collection_rate


summary_stats = {
    'avg_resource_collection_rate': {
        'minerals': {1: 0, 2: 0},
        'gas': {1: 0, 2: 0},
    },
    'avg_unspent_resources': {
        'minerals': {1: 0, 2: 0},
        'gas': {1: 0, 2: 0},
    },
    'resources_lost': {
        'minerals': {1: 0, 2: 0},
        'gas': {1: 0, 2: 0},
    },
    'workers_produced': {1: 0, 2: 0},
    'workers_killed': {1: 0, 2: 0},
    'workers_lost': {1: 0, 2: 0},
}


mock_player2 = Player(2, None, None, None, None, None)
mock_player2.unspent_resources['gas'].append(500)
mock_player2.unspent_resources['minerals'].append(800)
mock_player2.collection_rate['gas'].append(1200)
mock_player2.collection_rate['minerals'].append(1500)

mock_player3 = Player(1, None, None, None, None, None)
mock_player3.unspent_resources['gas'].append(500)
mock_player3.unspent_resources['minerals'].append(800)
mock_player3.collection_rate['gas'].append(1200)
mock_player3.collection_rate['minerals'].append(1500)


summary_stats_testdata = [
    (
        mock_player2,
        {
            'avg_resource_collection_rate': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'avg_unspent_resources': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'resources_lost': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'workers_produced': {1: 0, 2: 0},
            'workers_killed': {1: 0, 2: 0},
            'workers_lost': {1: 0, 2: 0},
        },
        100,
        {
            '_event': 'NNet.Replay.Tracker.SPlayerStatsEvent',
            '_gameloop': 1,
            'm_stats': {
                'm_scoreValueMineralsCurrent': 0,
                'm_scoreValueVespeneCurrent': 0,
                'm_scoreValueMineralsCollectionRate': 0,
                'm_scoreValueVespeneCollectionRate': 0,
                'm_scoreValueMineralsLostArmy': 0,
                'm_scoreValueVespeneLostArmy': 0,
                'm_scoreValueWorkersActiveCount': 12,
            },
        },
        summary_stats,
    ),
    (
        mock_player2,
        {
            'avg_resource_collection_rate': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'avg_unspent_resources': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'resources_lost': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'workers_produced': {1: 0, 2: 0},
            'workers_killed': {1: 0, 2: 0},
            'workers_lost': {1: 0, 2: 0},
        },
        100,
        {
            '_event': 'NNet.Replay.Tracker.SPlayerStatsEvent',
            '_gameloop': 100,
            'm_stats': {
                'm_scoreValueMineralsCurrent': 0,
                'm_scoreValueVespeneCurrent': 0,
                'm_scoreValueMineralsCollectionRate': 0,
                'm_scoreValueVespeneCollectionRate': 0,
                'm_scoreValueMineralsLostArmy': 0,
                'm_scoreValueVespeneLostArmy': 0,
                'm_scoreValueWorkersActiveCount': 12,
            },
        },
        {
            'avg_resource_collection_rate': {
                'minerals': {1: 0, 2: 1500},
                'gas': {1: 0, 2: 1200},
            },
            'avg_unspent_resources': {
                'minerals': {1: 0, 2: 800},
                'gas': {1: 0, 2: 500},
            },
            'resources_lost': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'workers_produced': {1: 0, 2: 0},
            'workers_killed': {1: 0, 2: 0},
            'workers_lost': {1: 0, 2: 0},
        },
    ),
    (
        mock_player3,
        {
            'avg_resource_collection_rate': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'avg_unspent_resources': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'resources_lost': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'workers_produced': {1: 0, 2: 0},
            'workers_killed': {1: 0, 2: 0},
            'workers_lost': {1: 0, 2: 0},
        },
        100,
        {
            '_event': 'NNet.Replay.Tracker.SPlayerStatsEvent',
            '_gameloop': 100,
            'm_stats': {
                'm_scoreValueMineralsCurrent': 0,
                'm_scoreValueVespeneCurrent': 0,
                'm_scoreValueMineralsCollectionRate': 0,
                'm_scoreValueVespeneCollectionRate': 0,
                'm_scoreValueMineralsLostArmy': 0,
                'm_scoreValueVespeneLostArmy': 0,
                'm_scoreValueWorkersActiveCount': 12,
            },
        },
        {
            'avg_resource_collection_rate': {
                'minerals': {1: 1500, 2: 0},
                'gas': {1: 1200, 2: 0},
            },
            'avg_unspent_resources': {
                'minerals': {1: 800, 2: 0},
                'gas': {1: 500, 2: 0},
            },
            'resources_lost': {
                'minerals': {1: 0, 2: 0},
                'gas': {1: 0, 2: 0},
            },
            'workers_produced': {1: 0, 2: 0},
            'workers_killed': {1: 0, 2: 0},
            'workers_lost': {1: 0, 2: 0},
        },
    ),
]


@pytest.mark.parametrize(
    "player, summary_stats, game_length, event, expected_summary_stats",
    summary_stats_testdata,
)
def test_parse_event_summary_stats(
    player,
    summary_stats,
    game_length,
    event,
    expected_summary_stats,
):
    gameloop = event['_gameloop']
    unspent_resources = player.unspent_resources
    collection_rate = player.collection_rate

    if gameloop == game_length:
        summary_stats['resources_lost']['minerals'][player.player_id] = event['m_stats']['m_scoreValueMineralsLostArmy']
        summary_stats['resources_lost']['gas'][player.player_id] = event['m_stats']['m_scoreValueVespeneLostArmy']

        player_minerals = unspent_resources['minerals']
        player_gas = unspent_resources['gas']
        summary_stats['avg_unspent_resources']['minerals'][player.player_id] = round(
            sum(player_minerals)/len(player_minerals), 1
        )
        summary_stats['avg_unspent_resources']['gas'][player.player_id] = round(
            sum(player_gas)/len(player_gas), 1
        )

        player_minerals_collection = collection_rate['minerals']
        player_gas_collection = collection_rate['gas']
        summary_stats['avg_resource_collection_rate']['minerals'][player.player_id] = round(
            sum(player_minerals_collection)/len(player_minerals_collection), 1
        )
        summary_stats['avg_resource_collection_rate']['gas'][player.player_id] = round(
            sum(player_gas_collection)/len(player_gas_collection), 1
        )

        # don't need to calculate sq for this unit test
        #
        # total_collection_rate = summary_stats['avg_resource_collection_rate']['minerals'][player.player_id] + summary_stats['avg_resource_collection_rate']['gas'][player.player_id]
        # total_avg_unspent = summary_stats['avg_unspent_resources']['minerals'][player.player_id] + summary_stats['avg_unspent_resources']['gas'][player.player_id]
        # player_sq = player.calc_sq(unspent_resources=total_avg_unspent, collection_rate=total_collection_rate)
        # summary_stats['sq'][player.player_id] = player_sq

        current_workers = event['m_stats']['m_scoreValueWorkersActiveCount']
        workers_produced = summary_stats['workers_produced'][player.player_id]
        summary_stats['workers_lost'][player.player_id] = workers_produced + 12 - current_workers

    assert summary_stats == expected_summary_stats
