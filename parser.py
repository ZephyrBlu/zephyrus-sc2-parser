import mpyq
import json
import math
from s2protocol import versions
import heapq
from game.game import Game
from game.player_state import PlayerState
from utils import create_event, create_players, convert_time


def initial_summary_stats(game, metadata, detailed_info):
    summary_stats = {
        'mmr': {1: 0, 2: 0},
        'mmr_diff': {1: 0, 2: 0},
        'avg_resource_collection_rate': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'avg_unspent_resources': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'apm': {1: 0, 2: 0},
        'resources_lost': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'workers_produced': {1: 0, 2: 0},
        'workers_lost': {1: 0, 2: 0},
        'inject_count': {1: 0, 2: 0},
        'sq': {1: 0, 2: 0},
        'pac': {
            'per_min': {1: 0, 2: 0},
            'avg_action_latency': {1: 0, 2: 0},
            'avg_actions': {1: 0, 2: 0},
            'avg_gap': {1: 0, 2: 0},
        }
    }

    mmr_data = detailed_info['m_syncLobbyState']['m_userInitialData']
    if not mmr_data[1]['m_scaledRating'] or mmr_data[2]['m_scaledRating']:
        return None, None, None

    ranked_game = False
    player1_mmr = mmr_data[0]['m_scaledRating']
    player2_mmr = mmr_data[1]['m_scaledRating']
    for p in metadata['Players']:
        if player1_mmr and player2_mmr:
            ranked_game = True
        else:
            ranked_game = False

        if p['Result'] == 'Win':
            game.winner = p['PlayerID']

    for player in metadata['Players']:
        player_id = player['PlayerID']

        summary_stats['apm'][player_id] = player['APM']

        if mmr_data[player_id-1]['m_scaledRating']:
            summary_stats['mmr'][player_id] = mmr_data[player_id-1]['m_scaledRating']
        else:
            summary_stats['mmr'][player_id] = 0

    if ranked_game:
        summary_stats['mmr_diff'][1] = player1_mmr-player2_mmr
        summary_stats['mmr_diff'][2] = player2_mmr-player1_mmr

    return summary_stats


def setup(filename):
    archive = mpyq.MPQArchive(filename)

    # getting correct game version and protocol
    contents = archive.header['user_data_header']['content']

    header = versions.latest().decode_replay_header(contents)

    base_build = header['m_version']['m_baseBuild']
    protocol = versions.build(base_build)

    # accessing neccessary parts of file for data
    contents = archive.read_file('replay.tracker.events')
    details = archive.read_file('replay.details')
    gameInfo = archive.read_file('replay.game.events')
    init_data = archive.read_file('replay.initData')

    metadata = json.loads(archive.read_file('replay.gamemetadata.json'))

    # translating data into dict format info
    game_events = protocol.decode_replay_game_events(gameInfo)
    player_info = protocol.decode_replay_details(details)
    tracker_events = protocol.decode_replay_tracker_events(contents)
    detailed_info = protocol.decode_replay_initdata(init_data)

    # all info is returned as generators
    #
    # to paint the full picture of the game
    # both game and tracker events are needed
    # so they are combined then sorted in chronological order

    events = heapq.merge(game_events, tracker_events, key=lambda x: x['_gameloop'])
    events = sorted(events, key=lambda x: x['_gameloop'])

    for event in events:
        if event['_event'] == 'NNet.Game.SGameUserLeaveEvent':
            game_length = event['_gameloop']
            break

    return events, player_info, detailed_info, metadata, game_length, protocol


def parse_replay(filename):
    try:
        events, player_info, detailed_info, metadata, game_length, protocol = setup(filename)
        players = create_players(player_info, events)
    except ValueError as error:
        print('A ValueError occured:', error, 'unreadable header')
        return None, None, None
    except ImportError as error:
        print('An ImportError occured:', error, 'unsupported protocol')
        return None, None, None
    except KeyError as error:
        print('A KeyError error occured:', error, 'unreadable file info')
        return None, None, None

    game_map = player_info['m_title'].decode('utf-8')
    played_at = convert_time(player_info['m_timeUTC'])
    current_game = Game(
        players,
        game_map,
        played_at,
        math.floor(game_length/22.4),
        events,
        protocol
    )

    summary_stats = initial_summary_stats(current_game, metadata, detailed_info)

    current_tick = 0
    for event in events:
        gameloop = event['_gameloop']
        if gameloop <= game_length:
            current_event = create_event(current_game, event, protocol, summary_stats)
            if current_event:
                # print(event)
                # print('\n')

                result = current_event.parse_event()

                if result:
                    summary_stats = result

                # 112 = 5sec of game time
                players.sort()
                if gameloop >= current_tick or gameloop == game_length:
                    player1_state = PlayerState(
                        players[0],
                        gameloop
                    )

                    player2_state = PlayerState(
                        players[1],
                        gameloop
                    )

                    current_game.state.append((player1_state, player2_state))
                    current_game.timeline.append({
                        1: player1_state.summary,
                        2: player2_state.summary
                    })

                    current_tick += 112

    # for player in players:
    #     print(player.name)
    #     for k, v in current_game.state[-1][player.player_id - 1].summary['unit'].items():
    #         print(k, v)

    #     for k, v in current_game.state[-1][player.player_id - 1].summary['building'].items():
    #         print(k, v)
    #     print('\n')

    players_export = {}
    for player in players:
        del player.__dict__['pac_list']
        del player.__dict__['current_pac']
        players_export[player.player_id] = player

    metadata_export = {
        'time_played_at': current_game.played_at,
        'map': current_game.map,
        'game_length': current_game.game_length,
        'winner': current_game.winner
    }

    return players_export, current_game.timeline, summary_stats, metadata_export


# main('test_pvt.SC2Replay')
