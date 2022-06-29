import mpyq
import json
import math
import heapq
import copy
import logging
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import NamedTuple, Dict, Any, Union, List, Optional
from zephyrus_sc2_parser.s2protocol_fixed import versions
from zephyrus_sc2_parser.game import Game, GameObj, Player, PlayerState
from zephyrus_sc2_parser.utils import (
    _generate_initial_summary_stats,
    _import_gamedata,
    _get_map_info,
    _create_event,
    _create_players,
    _convert_time
)
from zephyrus_sc2_parser.exceptions import MissingMmrError, ReplayDecodeError, GameLengthNotFoundError

logger = logging.getLogger(__name__)

# this type information is here instead of dataclasses.py
# to prevent circular imports

# GameState = {
#     <player id>: {
#         <gamestate key>: <gamestate value>
#     }
# }
GameState = Dict[int, Dict[str, Any]]

# SummaryStat = {
#     <stat name>: {
#         <player id>: <stat value>
#     }
# }
SummaryStat = Dict[str, Dict[int, int]]


# NamedTuple over dataclass so that it can be spread on return
class Replay(NamedTuple):
    players: Dict[int, Player]
    timeline: List[GameState]
    engagements: List
    summary: Union[SummaryStat, Dict[str, SummaryStat]]
    metadata: Dict[str, Any]


@dataclass
class Selection:
    objects: List[GameObj]
    start: int
    end: Optional[int]


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


def _setup(filename, local, _test):
    archive = mpyq.MPQArchive(filename)

    # getting correct game version and protocol
    header_content = archive.header['user_data_header']['content']
    error = True

    for i in range(0, 5):
        try:
            header = versions.latest().decode_replay_header(header_content)
            base_build = header['m_version']['m_baseBuild']
            try:
                protocol = versions.build(base_build)
            except ImportError:
                # if the build can't be found, we fallback to the latest version
                protocol = versions.latest()

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

    # if no MMR then exit early
    mmr_data = detailed_info['m_syncLobbyState']['m_userInitialData']
    for p_id in range(1, 3):
        player = mmr_data[p_id - 1]
        if 'm_scaledRating' not in player or not player['m_scaledRating']:
            logger.warning(f'Player {p_id} ({player["m_name"].decode("utf-8")}) has no MMR')
            if not local:
                raise MissingMmrError('One or more players has no MMR. If you want to parse replays without MMR, add "local=True" as a keyword argument')

    # all info is returned as generators
    # to paint the full picture of the game, both game and tracker events are needed
    # so they are combined then sorted in chronological order

    events = heapq.merge(game_events, tracker_events, key=lambda x: x['_gameloop'])
    events = sorted(events, key=lambda x: x['_gameloop'])

    # need to create players before finding the game length
    # since it relies on having the player ids
    players = _create_players(player_info, events, _test)
    logger.info('Created players')

    losing_player_id = None
    for p in metadata['Players']:
        if p['Result'] == 'Loss':
            losing_player_id = p['PlayerID']

    game_length = None
    last_user_leave = None
    for event in events:
        if event['_event'] == 'NNet.Game.SGameUserLeaveEvent':
            # need to collect this info in the case that the game ends via all buildings being destroyed
            # in this case, a UserLeaveEvent does not occur for the losing player
            last_user_leave = event['_gameloop']
            if (
                # losing player will always be the first player to leave the replay
                event['_userid']['m_userId'] == players[losing_player_id].user_id
                # in a draw I'm guessing neither player wins or loses, not sure how it works though
                or losing_player_id is None
            ):
                logger.debug(f'Found UserLeaveEvent. Game length = {event["_gameloop"]}')
                game_length = event['_gameloop']
                break

    if not game_length and not last_user_leave:
        raise GameLengthNotFoundError('Could not find the length of the game')
    else:
        # we fallback to the last leave event in the case that we can't find when the losing player leaves
        game_length = last_user_leave

    return events, players, player_info, detailed_info, metadata, game_length, protocol


def parse_replay(filename: str, *, local=False, tick=112, network=True, _test=False) -> Replay:
    events, players, player_info, detailed_info, metadata, game_length, protocol = _setup(filename, local, _test)

    if player_info['m_title'] in non_english_maps:
        map_name = non_english_maps[player_info['m_title']]
    else:
        map_name = player_info['m_title'].decode('utf-8')

    played_at = _convert_time(player_info['m_timeUTC'])
    game_map = _get_map_info(player_info, map_name, network)
    logger.info('Fetched map data')

    current_game = Game(
        players,
        game_map,
        played_at,
        game_length,
        events,
        protocol,
        _import_gamedata(protocol),
    )
    summary_stats = _generate_initial_summary_stats(
        current_game,
        metadata,
        detailed_info['m_syncLobbyState']['m_userInitialData'],
    )
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
            # if summary_stats are modified they are returned from parse_event
            # this only occurs for ObjectEvents and PlayerStatsEvents
            result = current_event.parse_event()
            logger.debug(f'Finished parsing event')

            if result:
                summary_stats = result

            if current_event.player and current_event.player.current_selection:
                player = current_event.player

                # empty list of selections i.e. first selection
                if not player.selections:
                    player.selections.append(
                        Selection(
                            player.current_selection,
                            gameloop,
                            None,
                        )
                    )

                # if the time and player's current selection has changed
                # update it and add the new selection
                # 2 gameloops ~ 0.09s
                elif (
                    gameloop - player.selections[-1].start >= 2
                    and player.current_selection != player.selections[-1].objects
                ):
                    player.selections[-1].end = gameloop
                    player.selections.append(
                        Selection(
                            player.current_selection,
                            gameloop,
                            None,
                        )
                    )

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

            # tick = kwarg value for timeline tick size
            # default tick = 112 (~5sec of game time)
            current_tick += tick

        # this condition is last to allow game/timeline state to be recorded at the end of the game
        if gameloop == game_length:
            logger.info('Reached end of the game')
            logger.debug(f'Current gameloop: {gameloop}, game length: {game_length}')
            break

    # ----- first iteration of parsing finished, start secondary parsing -----

    # aggregate all created units from game objs
    queues = []
    all_created_units = {1: [], 2: []}
    for p_id, player in players.items():
        for obj in player.objects.values():
            if obj._created_units:
                all_created_units[p_id].extend(obj._created_units)
    all_created_units[1].sort(key=lambda x: x.train_time)
    all_created_units[2].sort(key=lambda x: x.train_time)

    for p_id, player in players.items():
        if player.race == 'Zerg':
            # deepcopy to prevent mutating original objects by reference
            filtered_created_units = copy.deepcopy(all_created_units[p_id])
            current_larva = deque()
            for created_unit in all_created_units[p_id]:
                if not current_larva:
                    current_larva.appendleft(created_unit)
                    continue

                # if next unit is from the same building and has a train time specifically
                # 4 gameloops after the previous unit, it means these larva are from injects
                if (
                    created_unit.building == current_larva[-1].building
                    and created_unit.train_time == current_larva[-1].train_time + 4
                ):
                    current_larva.appendleft(created_unit)
                    continue

                # 3 larva = 1 inject
                # remove inject larva from created units
                if len(current_larva) == 3:
                    for obj in current_larva:
                        filtered_created_units.remove(obj)

                    # reset for next set of inject larva
                    current_larva = deque()

            # update created units to non-inject larva only
            all_created_units[p_id] = filtered_created_units

    created_unit_pos = {1: 0, 2: 0}
    total_downtime = {1: 0, 2: 0}
    current_downtime = {1: 0, 2: 0}
    idle_production_gameloop = {}
    for gameloop in range(0, game_length + 1):
        player_queues = {
            'gameloop': gameloop,
            1: {
                'supply_blocked': False,
                'queues': {},
                'downtime': {
                    'current': 0,
                    'total': 0,
                },
            },
            2: {
                'supply_blocked': False,
                'queues': {},
                'downtime': {
                    'current': 0,
                    'total': 0,
                },
            },
        }
        for p_id, player_units in all_created_units.items():
            # using OrderedDict to preserve order of obj creation
            # want command structures in order of when each base was created
            copied_queues = OrderedDict()
            # need to do this for perf so that queue itself is a new object
            # but references to objects inside queue are preserved
            if queues:
                for building, queue in queues[-1][p_id]['queues'].items():
                    copied_queues[building] = copy.copy(queue)
            current_queues = copied_queues

            # removing finished units from queue for this gameloop
            for building_queue in current_queues.values():
                for i in range(len(building_queue) - 1, -1, -1):
                    queued_unit = building_queue[i]
                    if queued_unit.birth_time <= gameloop:
                        building_queue.pop()

            # adding newly queued units for this gameloop
            # start from unit after last unit to be queued
            for i in range(created_unit_pos[p_id], len(player_units)):
                created_unit = player_units[i]

                # this means we're at the last unit and it's already been queued
                if (
                    gameloop > created_unit.train_time
                    and i == len(player_units) - 1
                ):
                    # set unit position pointer to len(player_units) to prevent further iteration
                    created_unit_pos[p_id] = i + 1
                    break

                # the rest of the recorded units are yet to be trained if train_time greater
                if created_unit.train_time > gameloop:
                    # this is next unit to be queued
                    created_unit_pos[p_id] = i
                    break

                if created_unit.building not in player_queues:
                    current_queues[created_unit.building] = deque()
                current_queues[created_unit.building].appendleft(created_unit.obj)
            player_queues[p_id]['queues'] = current_queues

        # if either of the queues have changed, update them
        if (
            not queues
            or queues[-1][1]['queues'] != player_queues[1]['queues']
            or queues[-1][2]['queues'] != player_queues[2]['queues']
        ):
            for p_id in range(1, 3):
                # current downtime must be recalculated every gameloop
                current_downtime[p_id] = 0
                updated_total_downtime = total_downtime[p_id]

                for building, queue in player_queues[p_id]['queues'].items():
                    # set initial state of idle gameloops
                    if building not in idle_production_gameloop:
                        idle_production_gameloop[building] = None

                    if idle_production_gameloop[building]:
                        current_downtime[p_id] += player_queues['gameloop'] - idle_production_gameloop[building]

                    # reset building idle gameloop if we have something queued now
                    # can also now add this building's idle time to total_downtime, since this idle period has ended
                    if queue and idle_production_gameloop[building]:
                        updated_total_downtime += player_queues['gameloop'] - idle_production_gameloop[building]
                        idle_production_gameloop[building] = None

                    # if we have an empty queue (i.e. idle production)
                    # and this is a new instance of idle time
                    if not queue and not idle_production_gameloop[building]:
                        idle_production_gameloop[building] = player_queues['gameloop']

                # update idle time counters
                player_queues[p_id]['downtime']['total'] = total_downtime[p_id] + current_downtime[p_id]
                player_queues[p_id]['downtime']['current'] = current_downtime[p_id]
                total_downtime[p_id] = updated_total_downtime
            queues.append(player_queues)

    for player in players.values():
        current_supply_block = 0
        for queue_state in queues:
            is_queued = False
            gameloop = queue_state['gameloop']
            player_queues = queue_state[player.player_id]['queues']
            for queue in player_queues.values():
                if queue:
                    is_queued = True

            # if all queues aren't active, we may be supply blocked
            # Zerg supply block aren't related to larva though
            if not is_queued or player.race == 'Zerg':
                for i in range(current_supply_block, len(player._supply_blocks)):
                    supply_block = player._supply_blocks[i]

                    # there is no way for this supply block to have occurred yet, so skip to next queue state
                    if gameloop < supply_block['start']:
                        break

                    # if this gameloop is inside supply block
                    if supply_block['start'] <= gameloop <= supply_block['end']:
                        queue_state[player.player_id]['supply_blocked'] = True

                        # supply block may span over gameloops, so start again at same block
                        current_supply_block = i
                        break

    for player in players.values():
        player_queues = []
        for queue_state in queues:
            current_queue = {
                'gameloop': queue_state['gameloop'],
                'supply_blocked': queue_state[player.player_id]['supply_blocked'],
                'queues': queue_state[player.player_id]['queues'],
                'downtime': queue_state[player.player_id]['downtime'],
            }
            player_queues.append(current_queue)
        player.queues = player_queues

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
            if 'creep' in current_game.timeline[-1][player.player_id]['race']:
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
        'played_at': current_game.played_at,
        'map': current_game.map.name,
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
