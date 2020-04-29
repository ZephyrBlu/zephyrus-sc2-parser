import mpyq
import json
import math
import heapq
from zephyrus_sc2_parser.s2protocol_fixed import versions
from zephyrus_sc2_parser.game.game import Game
from zephyrus_sc2_parser.game.player_state import PlayerState
from zephyrus_sc2_parser.utils import create_event, create_players, convert_time
import logging


non_english_maps = {
    b'\xec\x95\x84\xed\x81\xac\xeb\xa1\x9c\xed\x8f\xb4\xeb\xa6\xac\xec\x8a\xa4 \x2d \xeb\x9e\x98\xeb\x8d\x94': 'Acropolis LE',
    b'\xeb\x94\x94\xec\x8a\xa4\xec\xbd\x94 \xeb\xb8\x94\xeb\x9f\xac\xeb\x93\x9c\xeb\xb0\xb0\xec\x8a\xa4 \x2d \xeb\x9e\x98\xeb\x8d\x94': 'Disco Bloodbath LE',
    b'\xed\x8a\xb8\xeb\x9d\xbc\xec\x9d\xb4\xed\x8a\xbc \x2d \xeb\x9e\x98\xeb\x8d\x94': 'Triton LE',
    b'\xec\x9c\x88\xed\x84\xb0\xec\x8a\xa4 \xea\xb2\x8c\xec\x9d\xb4\xed\x8a\xb8 \x2d \xeb\x9e\x98\xeb\x8d\x94': "Winter's Gate LE",
    b'\xec\x8d\xac\xeb\x8d\x94\xeb\xb2\x84\xeb\x93\x9c \x2d \xeb\x9e\x98\xeb\x8d\x94': 'Thunderbird LE',
    b'\xec\x9d\xb4\xed\x8e\x98\xeb\xa8\xb8\xeb\xa1\xa0 \x2d \xeb\x9e\x98\xeb\x8d\x94': 'Ephemeron LE',
    b'\xec\x9b\x94\xeb\x93\x9c \xec\x98\xa4\xeb\xb8\x8c \xec\x8a\xac\xeb\xa6\xac\xed\x8d\xbc\xec\x8a\xa4 \x2d \xeb\x9e\x98\xeb\x8d\x94': 'World of Sleepers LE',
}


def initial_summary_stats(game, metadata, detailed_info, local=False):
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
        'resources_collected': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0},
        },
        'workers_produced': {1: 0, 2: 0},
        'workers_killed': {1: 0, 2: 0},
        'workers_lost': {1: 0, 2: 0},
        'supply_block': {1: 0, 2: 0},
        'inject_count': {1: 0, 2: 0},
        'sq': {1: 0, 2: 0},
        'avg_pac_per_min': {1: 0, 2: 0},
        'avg_pac_action_latency': {1: 0, 2: 0},
        'avg_pac_actions': {1: 0, 2: 0},
        'avg_pac_gap': {1: 0, 2: 0},
    }

    mmr_data = detailed_info['m_syncLobbyState']['m_userInitialData']
    if not mmr_data[0]['m_scaledRating'] or not mmr_data[1]['m_scaledRating']:
        logging.debug('One or more players has no MMR')
        if not local:
            return None

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

    header = None

    error = True
    for i in range(0, 5):
        try:
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
            error = False
            break
        except Exception as e:
            logging.error(f'An error occurred while decoding: {e}')
            pass
    if error:
        logging.critical('Replay could not be decoded')
        return None, None, None, None, None, None

    # all info is returned as generators
    #
    # to paint the full picture of the game
    # both game and tracker events are needed
    # so they are combined then sorted in chronological order

    events = heapq.merge(game_events, tracker_events, key=lambda x: x['_gameloop'])
    events = sorted(events, key=lambda x: x['_gameloop'])

    for event in events:
        # if 'SCameraUpdateEvent' not in event['_event']:  # == 'NNet.Replay.Tracker.SUnitPositionsEvent':
        print(event)
        print('\n')

    for event in events:
        if event['_event'] == 'NNet.Game.SGameUserLeaveEvent':
            game_length = event['_gameloop']
            break

    return events, player_info, detailed_info, metadata, game_length, protocol


def parse_replay(filename, *, local=False, detailed=False):
    try:
        events, player_info, detailed_info, metadata, game_length, protocol = setup(filename)

        if events is None:
            logging.critical('Aborting replay due to bad decode...')
            return None, None, None, None

        players = create_players(player_info, events)
    except ValueError as error:
        logging.critical('A ValueError occured:', error, 'unreadable header')
        return None, None, None, None
    except ImportError as error:
        logging.critical('An ImportError occured:', error, 'unsupported protocol')
        return None, None, None, None
    except KeyError as error:
        logging.critical('A KeyError error occured:', error, 'unreadable file info')
        return None, None, None, None

    if player_info['m_title'] in non_english_maps:
        game_map = non_english_maps[player_info['m_title']]
    else:
        game_map = player_info['m_title'].decode('utf-8')
    played_at = convert_time(player_info['m_timeUTC'])

    if not players:
        logging.debug('Aborting replay due to <2 players...')
        return None, None, None, None

    current_game = Game(
        players,
        game_map,
        played_at,
        game_length,
        events,
        protocol
    )

    summary_stats = initial_summary_stats(current_game, metadata, detailed_info, local)

    if summary_stats is None:
        logging.debug('Aborting replay due to missing MMR value(s)')
        return None, None, None, None

    action_events = [
        'NNet.Game.SControlGroupUpdateEvent',
        'NNet.Game.SSelectionDeltaEvent',
        'NNet.Game.SCmdEvent',
        'NNet.Game.SCommandManagerStateEvent',
    ]

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

                if current_event.type in action_events and current_event.player and current_event.player.current_pac:
                    current_event.player.current_pac.actions.append(gameloop)

                # 112 = 5sec of game time
                players.sort()
                if gameloop >= current_tick or gameloop == game_length:
                    player1_state = PlayerState(
                        players[0],
                        gameloop,
                    )

                    player2_state = PlayerState(
                        players[1],
                        gameloop,
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
        summary_stats = player.calc_pac(summary_stats, game_length)

        if not detailed:
            del player.__dict__['pac_list']
            del player.__dict__['current_pac']
            del player.__dict__['objects']
            del player.__dict__['current_selection']
            del player.__dict__['control_groups']
            del player.__dict__['active_ability']
            del player.__dict__['unspent_resources']
            del player.__dict__['collection_rate']
        players_export[player.player_id] = player

        for p in players:
            if p.player_id != player.player_id:
                summary_stats['workers_killed'][p.player_id] = summary_stats['workers_lost'][player.player_id]

    metadata_export = {
        'time_played_at': current_game.played_at,
        'map': current_game.map,
        'game_length': math.floor(current_game.game_length/22.4),
        'winner': current_game.winner
    }

    return players_export, current_game.timeline, summary_stats, metadata_export
