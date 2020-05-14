import mpyq
import json
import math
import heapq
from zephyrus_sc2_parser.s2protocol_fixed import versions
from zephyrus_sc2_parser.game.game import Game
from zephyrus_sc2_parser.game.player_state import PlayerState
from zephyrus_sc2_parser.utils import (
    import_gamedata, get_map_info, create_event, create_players, convert_time
)
import logging

is_engagement_simulator_installed = False
try:
    from sc2_simulator import simulate_engagement
    is_engagement_simulator_installed = True
except ImportError:
    pass

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
        'avg_resource_collection_rate': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'avg_unspent_resources': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'apm': {1: 0, 2: 0},
        'spm': {1: 0, 2: 0},
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
        'sq': {1: 0, 2: 0},
        'avg_pac_per_min': {1: 0, 2: 0},
        'avg_pac_action_latency': {1: 0, 2: 0},
        'avg_pac_actions': {1: 0, 2: 0},
        'avg_pac_gap': {1: 0, 2: 0},
        'race': {1: {}, 2: {}},
    }

    mmr_data = detailed_info['m_syncLobbyState']['m_userInitialData']
    if not mmr_data[0]['m_scaledRating'] or not mmr_data[1]['m_scaledRating']:
        logging.debug('One or more players has no MMR')
        if not local:
            return None

    for p in metadata['Players']:
        if p['Result'] == 'Win':
            game.winner = p['PlayerID']

    for player in metadata['Players']:
        player_id = player['PlayerID']

        summary_stats['apm'][player_id] = player['APM']

        if mmr_data[player_id-1]['m_scaledRating']:
            summary_stats['mmr'][player_id] = mmr_data[player_id-1]['m_scaledRating']
        else:
            summary_stats['mmr'][player_id] = 0

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

    # for event in events:
    #     # if event['_event'] == 'NNet.Game.SCmdEvent':  # == 'NNet.Replay.Tracker.SUnitPositionsEvent':
    #     print(event)
    #     print('\n')

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
            return None, None, None, None, None

        players = create_players(player_info, events)
    except ValueError as error:
        logging.critical('A ValueError occured:', error, 'unreadable header')
        return None, None, None, None, None
    except ImportError as error:
        logging.critical('An ImportError occured:', error, 'unsupported protocol')
        return None, None, None, None, None
    except KeyError as error:
        logging.critical('A KeyError error occured:', error, 'unreadable file info')
        return None, None, None, None, None

    if not players:
        logging.debug('Aborting replay due to <2 players...')
        return None, None, None, None, None

    if player_info['m_title'] in non_english_maps:
        game_map = non_english_maps[player_info['m_title']]
    else:
        game_map = player_info['m_title'].decode('utf-8')

    played_at = convert_time(player_info['m_timeUTC'])
    map_info = get_map_info(player_info, game_map)

    if not map_info:
        logging.debug('Aborting replay due to missing map data')
        return None, None, None, None, None

    current_game = Game(
        players,
        map_info,
        played_at,
        game_length,
        events,
        protocol,
        import_gamedata(protocol),
    )

    summary_stats = initial_summary_stats(current_game, metadata, detailed_info, local)

    if summary_stats is None:
        logging.debug('Aborting replay due to missing MMR value(s)')
        return None, None, None, None, None

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
                result = current_event.parse_event()

                if result:
                    summary_stats = result

                if current_event.type in action_events and current_event.player and current_event.player.current_pac:
                    current_event.player.current_pac.actions.append(gameloop)

                # 112 = 5sec of game time
                if gameloop >= current_tick or gameloop == game_length:
                    player1_state = PlayerState(
                        current_game,
                        players[1],
                        gameloop,
                    )

                    player2_state = PlayerState(
                        current_game,
                        players[2],
                        gameloop,
                    )

                    current_game.state.append((player1_state, player2_state))
                    current_game.timeline.append({
                        1: player1_state.summary,
                        2: player2_state.summary
                    })

                    player_units = {1: [], 2: []}
                    for p_id, p in players.items():
                        for obj in p.objects.values():
                            if obj.status == 'live':
                                player_units[p_id].append(obj.name)

                    current_game.engagements.append((
                        player_units[1],
                        player_units[2],
                        players[1].upgrades,
                        players[2].upgrades,
                        gameloop,
                    ))

                    current_tick += 112

    engagement_analysis = []
    if is_engagement_simulator_installed:
        engagement_outcomes = simulate_engagement(current_game.engagements)
        for winner, unit_health, gameloop in engagement_outcomes:
            total_health = {1: (0, 0), 2: (0, 0)}
            for unit in unit_health:
                total_health[unit[0]] = (
                    total_health[unit[0]][0] + unit[2],
                    total_health[unit[0]][1] + unit[3],
                )

            if total_health[1][1] > 0 and total_health[2][1] > 0:
                engagement_analysis.append({
                    'winner': winner,
                    'health': total_health[winner],
                    'remaining_health':  round((total_health[winner][0] / total_health[winner][1]), 3),
                    'gameloop': gameloop,
                })

    players_export = {}
    for p_id, player in players.items():
        summary_stats = player.calc_pac(summary_stats, game_length)
        summary_stats['spm'][player.player_id] = player.calc_spm(current_game.game_length)

        opp_id = 1 if p_id == 2 else 2

        if player.race == 'Zerg':
            print(current_game.timeline[-1][player.player_id]['race'])
            summary_stats['race'][player.player_id]['inject_efficiency'] = current_game.timeline[-1][player.player_id]['race']['inject_efficiency']
            summary_stats['race'][player.player_id]['avg_idle_larva'] = round(sum(player.idle_larva) / len(player.idle_larva), 1)
            summary_stats['race'][player.player_id]['creep'] = current_game.timeline[-1][player.player_id]['race']['creep']

        elif player.race == 'Protoss':
            opp_player = players[opp_id]

            protoss_splash = {
                'HighTemplar': (0, 0),
                'Disruptor': (0, 0),
                'Colossus': (0, 0),
            }

            units = current_game.gamedata['units']

            for obj in opp_player.objects.values():
                if obj.killed_by and obj.killed_by.name in protoss_splash:
                    protoss_splash[obj.killed_by] = (
                        protoss_splash[obj.killed_by][0] + units[obj.name]['mineral_cost'],
                        protoss_splash[obj.killed_by][1] + units[obj.name]['gas_cost'],
                    )

            splash_efficiency = {}
            for splash_unit, resources_killed in protoss_splash.items():
                # if not default
                if resources_killed != (0, 0):
                    unit_mineral_cost = units[splash_unit]['mineral_cost']
                    unit_gas_cost = units[splash_unit]['gas_cost']

                    splash_efficiency[splash_unit] = (
                        round(resources_killed[0] / unit_mineral_cost, 2),
                        round(resources_killed[1] / unit_gas_cost, 2),
                    )

            if splash_efficiency:
                summary_stats['race'][player.player_id]['splash_efficiency'] = splash_efficiency

        if 'energy' in current_game.timeline[-1][player.player_id]['race']:
            energy_stats = current_game.timeline[-1][player.player_id]['race']['energy']
            energy_efficiency = {}
            energy_idle_time = {}

            for obj_name, energy_info in energy_stats.items():
                energy_efficiency[obj_name] = []
                energy_idle_time[obj_name] = []
                for obj_data in energy_info:
                    energy_efficiency[obj_name].append(obj_data[1])
                    energy_idle_time[obj_name].append(obj_data[2])

            summary_stats['race'][player.player_id]['energy'] = {
                'efficiency': energy_efficiency,
                'idle_time': energy_idle_time,
            }

        if 'warpgate_efficiency' in current_game.timeline[-1][player.player_id]['race']:
            warpgate_efficiency = current_game.timeline[-1][player.player_id]['race']['warpgate_efficiency']
            summary_stats['race'][player.player_id]['warpgate'] = {
                'efficiency': warpgate_efficiency[0],
                'idle_time': warpgate_efficiency[1],
            }

        if not detailed:
            del player.__dict__['pac_list']
            del player.__dict__['current_pac']
            del player.__dict__['objects']
            del player.__dict__['current_selection']
            del player.__dict__['control_groups']
            del player.__dict__['warpgate_cooldowns']
            del player.__dict__['warpgate_efficiency']
            del player.__dict__['active_ability']
            del player.__dict__['unspent_resources']
            del player.__dict__['collection_rate']
            del player.__dict__['resources_collected']
            del player.__dict__['supply']
            del player.__dict__['supply_cap']
        players_export[player.player_id] = player

        summary_stats['workers_killed'][opp_id] = summary_stats['workers_lost'][player.player_id]

    metadata_export = {
        'time_played_at': current_game.played_at,
        'map': current_game.map['name'],
        'game_length': math.floor(current_game.game_length/22.4),
        'winner': current_game.winner
    }

    return players_export, current_game.timeline, engagement_analysis, summary_stats, metadata_export
