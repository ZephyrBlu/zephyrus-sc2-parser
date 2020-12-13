import mpyq
import json
import math
import heapq
import logging
from zephyrus_sc2_parser.s2protocol_fixed import versions
from zephyrus_sc2_parser.game import Game, GameObj, PlayerState
from zephyrus_sc2_parser.dataclasses import Replay
from zephyrus_sc2_parser.utils import (
    _generate_initial_summary_stats,
    _import_gamedata,
    _get_map_info,
    _create_event,
    _create_players,
    _convert_time
)
from zephyrus_sc2_parser.exceptions import ReplayDecodeError, GameLengthNotFoundError

logger = logging.getLogger(__name__)

# intl map names
# should probably figure out a way to automate this for each map pool
MAP_NAMES = {
    "Eternal Empire LE": (
        "永恆帝國 - 天梯版",
        "Empire éternel EC",
        "Ewiges Imperium LE",
        "이터널 엠파이어 - 래더",
        "Imperio eterno EE",
        'Imperio eterno EJ',
        '永恒帝国-天梯版',
        'Вечная империя РВ',
    ),
    "World of Sleepers LE": (
        "Welt der Schläfer LE",
        "休眠者之境 - 天梯版",
        "Domaine des dormeurs EC",
        "월드 오브 슬리퍼스 - 래더",
        'Mundo de durmientes EE',
    ),
    "Triton LE": (
        "Triton EC",
        "海神信使 - 天梯版",
        "트라이튼 - 래더",
        'Tritón EE',
    ),
    "Nightshade LE": (
        "Nocny Mrok ER",
        "毒茄樹叢 - 天梯版",
        "나이트쉐이드 - 래더",
        'Belladona EE',
        'Belladone EC',
    ),
    "Zen LE": (
        "젠 - 래더",
        'Zen EC',
        'Zen EE',
        'Zen EJ',
    ),
    "Ephemeron LE": (
        "Efemeryda ER",
        "이페머론 - 래더",
        'Efímero EE',
        'Éphémèrion EC',
    ),
    "Golden Wall LE": (
        "골든 월 - 래더",
        '黄金墙-天梯版',
        'Mur doré EC',
    ),
    "Ever Dream LE": (
        "에버 드림 - 래더",
        "永恒梦境-天梯版",
        "Помечтай РВ",
    ),
    "Simulacrum LE": (
        "시뮬레이크럼 - 래더",
        'Simulacre EC',
        'Simulacro EE',
    ),
    "Pillars of Gold LE": (
        '黄金之柱-天梯版',
        "Piliers d'or EC",
        '필러스 오브 골드 - 래더',
    ),
    "Submarine LE": (
        '潜水艇-天梯版',
        "Подводный мир РВ",
        "Sous-marin EC",
        '서브머린 - 래더',
    ),
    "Deathaura LE": (
        '死亡光环-天梯版',
        "Aura de mort EC",
        '데스오라 - 래더',
    ),
    "Ice and Chrome LE": (
        '冰雪合金-天梯版',
        'Лед и хром РВ',
        "Glace et chrome EC",
        '아이스 앤 크롬 - 래더',
    ),
}

non_english_maps = {}
for map_name, non_eng_name_tuple in MAP_NAMES.items():
    for non_eng_map_name in non_eng_name_tuple:
        non_english_maps[non_eng_map_name.encode('utf-8')] = map_name


def _setup(filename):
    archive = mpyq.MPQArchive(filename)

    # getting correct game version and protocol
    header_content = archive.header['user_data_header']['content']
    error = True

    for i in range(0, 5):
        try:
            header = versions.latest().decode_replay_header(header_content)
            base_build = header['m_version']['m_baseBuild']
            protocol = versions.build(base_build)

            # accessing neccessary parts of file for data
            contents = archive.read_file('replay.tracker.events')
            details = archive.read_file('replay.details')
            game_info = archive.read_file('replay.game.events')
            init_data = archive.read_file('replay.initData')
            metadata = json.loads(archive.read_file('replay.gamemetadata.json'))

            # translating data into dict format info
            # look into using detailed_info['m_syncLobbyState']['m_userInitialData']
            # instead of player_info for player names, clan tags, etc
            # maybe metadata['IsNotAvailable'] is useful for something?
            # metadata['duration'] could be replacement for game length?
            game_events = protocol.decode_replay_game_events(game_info)
            player_info = protocol.decode_replay_details(details)
            tracker_events = protocol.decode_replay_tracker_events(contents)
            detailed_info = protocol.decode_replay_initdata(init_data)
            error = False
            break

        # ValueError = unreadable header
        # ImportError = unsupported protocol
        # KeyError = unreadable file info
        except ValueError as e:
            logger.warning(f'Unreadable file header: {e}')
        except ImportError as e:
            logger.warning(f'Unsupported protocol: {e}')
        except KeyError as e:
            logger.warning(f'Unreadable file info: {e}')
    if error:
        logger.critical('Replay could not be decoded')
        raise ReplayDecodeError('Replay could not be decoded')

    logger.info('Parsed raw replay file')

    # all info is returned as generators
    # to paint the full picture of the game
    # both game and tracker events are needed
    # so they are combined then sorted in chronological order

    events = heapq.merge(game_events, tracker_events, key=lambda x: x['_gameloop'])
    events = sorted(events, key=lambda x: x['_gameloop'])

    game_length = None
    for event in events:
        if event['_event'] == 'NNet.Game.SGameUserLeaveEvent':
            logger.debug(f'Found UserLeaveEvent. Game length = {event["_gameloop"]}')
            game_length = event['_gameloop']
            break

    # don't know why some replays don't have an end event, they just end abruptly
    if not game_length:
        raise GameLengthNotFoundError('Could not find the length of the game')

    return events, player_info, detailed_info, metadata, game_length, protocol


def parse_replay(filename, *, local=False, creep=True, _test=False):
    events, player_info, detailed_info, metadata, game_length, protocol = _setup(filename)
    players = _create_players(player_info, events, _test)
    logger.info('Created players')

    if player_info['m_title'] in non_english_maps:
        game_map = non_english_maps[player_info['m_title']]
    else:
        game_map = player_info['m_title'].decode('utf-8')

    played_at = _convert_time(player_info['m_timeUTC'])
    map_info = _get_map_info(player_info, game_map, creep)
    logger.info('Fetched map data')

    current_game = Game(
        players,
        map_info,
        played_at,
        game_length,
        events,
        protocol,
        _import_gamedata(protocol),
    )
    summary_stats = _generate_initial_summary_stats(current_game, metadata, detailed_info, local)
    logger.info('Completed pre-parsing setup')

    # ----- core parsing logic -----

    action_events = [
        'NNet.Game.SControlGroupUpdateEvent',
        'NNet.Game.SSelectionDeltaEvent',
        'NNet.Game.SCmdEvent',
        'NNet.Game.SCommandManagerStateEvent',
    ]

    logger.info('Iterating through game events')

    current_tick = 0
    for event in events:
        gameloop = event['_gameloop']

        # create event object from JSON data
        # if the event isn't supported, continue iterating
        current_event = _create_event(current_game, event, protocol, summary_stats)
        if current_event:
            # parse_event extracts and processes event data to update Player/GameObj objects
            # if summary_stats are modified they are returned from parse_event. This only occurs for ObjectEvents and PlayerStatsEvents
            result = current_event.parse_event()
            logger.debug(f'Finished parsing event')

            if result:
                summary_stats = result

            if current_event.player and current_event.player.current_selection:
                player = current_event.player

                # empty list of selections i.e. first selection
                if not player.selections:
                    player.selections.append({
                        'selection': player.current_selection,
                        'start': gameloop,
                        'end': None,
                    })

                # if the time and player's current selection has changed
                # update it and add the new selection
                # 2 gameloops ~ 0.09s
                elif (
                    gameloop - player.selections[-1]['start'] >= 2
                    and player.current_selection != player.selections[-1]['selection']
                ):
                    player.selections[-1]['end'] = gameloop
                    player.selections.append({
                        'selection': player.current_selection,
                        'start': gameloop,
                        'end': None,
                    })

            if (
                current_event.type in action_events
                and current_event.player
                and current_event.player.current_pac
            ):
                current_event.player.current_pac.actions.append(gameloop)

        # every 5sec + at end of the game, record the game state
        if gameloop >= current_tick or gameloop == game_length:
            current_player_states = {}
            for player in players.values():
                player_state = PlayerState(
                    current_game,
                    player,
                    gameloop,
                )
                current_player_states[player.player_id] = player_state

            # if only 2 players, we can use workers_lost of the opposite players to get workers_killed
            if len(current_player_states) == 2:
                current_player_states[1].summary['workers_killed'] = current_player_states[2].summary['workers_lost']
                current_player_states[2].summary['workers_killed'] = current_player_states[1].summary['workers_lost']

            current_timeline_state = {}
            for state in current_player_states.values():
                current_timeline_state[state.player.player_id] = state.summary

            logger.debug(f'Created new game state at {gameloop}')

            current_game.state.append(tuple(current_player_states))
            current_game.timeline.append(current_timeline_state)
            logger.debug(f'Recorded new timeline state at {gameloop}')

            # 112 = 5sec of game time
            current_tick += 112

        # this condition is last to allow game/timeline state to be recorded at the end of the game
        if gameloop == game_length:
            logger.info('Reached end of the game')
            logger.debug(f'Current gameloop: {gameloop}, game length: {game_length}')
            break

    # ----- parsing finished, generating return data -----

    logger.info('Generating game stats')
    players_export = {}
    for player in players.values():
        summary_stats = player.calc_pac(summary_stats, game_length)
        summary_stats['spm'][player.player_id] = player.calc_spm(current_game.game_length)

        collection_rate_totals = list(map(
            lambda x: x[0] + x[1],
            zip(player.collection_rate['minerals'], player.collection_rate['gas']),
        ))
        if collection_rate_totals:
            summary_stats['max_collection_rate'][player.player_id] = max(collection_rate_totals)

        opp_id = 1 if player.player_id == 2 else 2

        if player.race == 'Zerg':
            if creep:
                summary_stats['race'][player.player_id]['creep'] = current_game.timeline[-1][player.player_id]['race']['creep']

            if 'inject_efficiency' in current_game.timeline[-1][player.player_id]['race']:
                summary_stats['race'][player.player_id]['inject_efficiency'] = current_game.timeline[-1][player.player_id]['race']['inject_efficiency']

            if len(player.idle_larva) == 0:
                summary_stats['race'][player.player_id]['avg_idle_larva'] = 0
            else:
                summary_stats['race'][player.player_id]['avg_idle_larva'] = round(sum(player.idle_larva) / len(player.idle_larva), 1)

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

        players_export[player.player_id] = player
        summary_stats['workers_killed'][opp_id] = summary_stats['workers_lost'][player.player_id]

    metadata_export = {
        'time_played_at': current_game.played_at,
        'map': current_game.map['name'],
        'game_length': math.floor(current_game.game_length / 22.4),
        'winner': current_game.winner
    }

    logger.info('Parsing completed')

    return Replay(
        players_export,
        current_game.timeline,
        [],
        summary_stats,
        metadata_export,
    )
