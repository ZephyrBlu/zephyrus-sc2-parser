import datetime
import math
import mpyq
import binascii
import requests
import struct
from pathlib import Path
from io import BytesIO
from importlib import import_module
from typing import Dict
from zephyrus_sc2_parser.events import (
    ObjectEvent,
    AbilityEvent,
    SelectionEvent,
    ControlGroupEvent,
    UpgradeEvent,
    CameraEvent,
    PlayerStatsEvent,
)
from zephyrus_sc2_parser.dataclasses import GameData, Map
from zephyrus_sc2_parser.game import Player
from zephyrus_sc2_parser.gamedata.map_info import maps
from zephyrus_sc2_parser.exceptions import PlayerCountError
import pytz
import logging

logger = logging.getLogger(__name__)

NON_ENGLISH_RACES = {
    '저그': 'Zerg',
    '异虫': 'Zerg',
    '蟲族': 'Zerg',
    '테란': 'Terran',
    '人類': 'Terran',
    '人类': 'Terran',
    'Terraner': 'Terran',
    'Терраны': 'Terran',
    '프로토스': 'Protoss',
    '神族': 'Protoss',
    'Protosi': 'Protoss',
    '星灵': 'Protoss',
    'Протоссы': 'Protoss',
}

non_english_races = {}
for non_eng_race, eng_race in NON_ENGLISH_RACES.items():
    non_english_races[non_eng_race.encode('utf8')] = eng_race


def _convert_time(windows_time):
    unix_epoch_time = math.floor(windows_time/10000000)-11644473600
    replay_datetime = datetime.datetime.fromtimestamp(unix_epoch_time).replace(tzinfo=pytz.utc)
    return replay_datetime


def _import_gamedata(protocol):
    protocol_name = protocol.__name__[8:]
    unit_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.unit_data')
    building_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.building_data')
    ability_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.ability_data')
    upgrade_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.upgrade_data')

    return GameData(
        unit_data.units,
        building_data.buildings,
        ability_data.abilities,
        upgrade_data.upgrades,
    )


def _generate_initial_summary_stats(game, metadata, mmr_data):
    summary_stats = {
        'mmr': {1: 0, 2: 0},
        'avg_resource_collection_rate': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'max_collection_rate': {1: 0, 2: 0},
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

    # setting winner of the game
    for p in metadata['Players']:
        if p['Result'] == 'Win':
            game.winner = p['PlayerID']

    # setting basic summary stats
    for player in metadata['Players']:
        player_id = player['PlayerID']
        summary_stats['apm'][player_id] = player['APM']

        if 'm_scaledRating' in mmr_data[player_id - 1]:
            summary_stats['mmr'][player_id] = mmr_data[player_id - 1]['m_scaledRating']
        else:
            summary_stats['mmr'][player_id] = None
    return summary_stats


def _create_players(player_info, events, test_flag):
    # get player name and race
    # workingSetSlotId correlates to playerIDs
    players = []
    races = ['Protoss', 'Terran', 'Zerg']

    # find and record players
    for count, player in enumerate(player_info['m_playerList']):
        if player['m_workingSetSlotId'] is None:
            new_player = Player(
                count,
                player['m_toon']['m_id'],
                player['m_toon']['m_region'],
                player['m_toon']['m_realm'],
                player['m_name'],
                player['m_race']
            )
            players.append(new_player)
        else:
            new_player = Player(
                player['m_workingSetSlotId'],
                player['m_toon']['m_id'],
                player['m_toon']['m_region'],
                player['m_toon']['m_realm'],
                player['m_name'].decode('utf-8'),
                player['m_race'].decode('utf-8')
            )
            players.append(new_player)

        if new_player.race not in races:
            new_player.race = non_english_races[new_player.race.encode('utf-8')]

    # first 2 events in every replay with 2 players is always setup for playerIDs
    # need to look at the setup to match player IDs to players
    setup_index = 0
    for setup_index, event in enumerate(events):
        if event['_event'] == 'NNet.Replay.Tracker.SPlayerSetupEvent':
            break

    # logic for translating user_id's into playerID's

    # if only one player then playerID is always 0
    if len(players) != 2:
        if test_flag and len(players) == 1:
            player_obj = players[0]
            player_obj.player_id = events[setup_index]['m_playerId']
            player_obj.user_id = events[setup_index]['m_userId']

            return {
                1: player_obj,
            }

        logger.warning('Replay does not contain exactly 2 players')
        raise PlayerCountError(f'There are {len(players)} in the replay. Only 2 player replays are supported')

    # if both user_id's larger than 2 then lowest user_id first, the largest
    elif min(players) > 2:
        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']

        player_obj = max(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index + 1]['m_playerId']
        player_obj.user_id = events[setup_index + 1]['m_userId']

    # if both user_id's under 2 then the largest is set as 2 and the smallest is set as 1
    # specifically in that order to prevent assignment conflicts
    elif max(players) < 2:
        player_obj = max(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index + 1]['m_playerId']
        player_obj.user_id = events[setup_index + 1]['m_userId']

        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']

    # else specific numbers don't matter and smallest user_id correlates to playerID of 1
    # and largest user_id correlates to playerID of 2
    # not sure if I need this
    else:
        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']

        player_obj = max(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index + 1]['m_playerId']
        player_obj.user_id = events[setup_index + 1]['m_userId']

    players.sort(key=lambda x: x.player_id)

    return {
        1: players[0],
        2: players[1],
    }


def _get_map_info(player_info: Dict, map_name: str, network_flag: bool) -> Map:
    game_map = Map(map_name)

    if map_name not in maps and network_flag:
        map_bytes = player_info['m_cacheHandles'][-1]
        server = map_bytes[4:8].decode('utf8').strip('\x00 ').lower()
        file_hash = binascii.b2a_hex(map_bytes[8:]).decode('utf8')
        file_type = map_bytes[0:4].decode('utf8')

        map_file = None
        for i in range(0, 5):
            map_response = requests.get(f'https://{server}-s2-depot.classic.blizzard.com/{file_hash}.{file_type}')
            if map_response.status_code == 200:
                map_file = BytesIO(map_response.content)
                break
            logger.warning(f'Could not fetch {map_name} map file. Retrying')

        if not map_file:
            logger.error(f'Failed to fetch {map_name} map file')
            return game_map

        map_archive = mpyq.MPQArchive(map_file)
        map_data = BytesIO(map_archive.read_file('MapInfo'))
        map_data.seek(4)

        # returns tuple of 32 byte unsigned integer
        unpack_int = struct.Struct('<I').unpack
        version = unpack_int(map_data.read(4))[0]
        if version >= 0x18:
            # trash bytes
            unpack_int(map_data.read(4))
            unpack_int(map_data.read(4))
        map_width = unpack_int(map_data.read(4))[0]
        map_height = unpack_int(map_data.read(4))[0]
        maps.update({
            map_name: {
                'width': map_width,
                'height': map_height,
            },
        })

        try:
            map_info_path = Path(__file__).resolve().parent / 'gamedata' / 'map_info.py'
            with open(map_info_path, 'w', encoding='utf-8') as map_info:
                map_info.write(f'maps = {maps}')
        except OSError:
            logger.warning('Could not write map details to file')

    # something may have gone wrong when trying to get map details
    # or network_flag may be False
    if map_name in maps:
        game_map.width = maps[map_name]['width']
        game_map.height = maps[map_name]['height']

    return game_map


def _create_event(game, event, protocol, summary_stats):
    object_events = [
        'NNet.Replay.Tracker.SUnitInitEvent',
        'NNet.Replay.Tracker.SUnitDoneEvent',
        'NNet.Replay.Tracker.SUnitBornEvent',
        'NNet.Replay.Tracker.SUnitDiedEvent',
        'NNet.Replay.Tracker.SUnitTypeChangeEvent'
    ]

    ability_events = [
        'NNet.Game.SCmdEvent',
        'NNet.Game.SCommandManagerStateEvent'
    ]

    if event['_event'] in object_events:
        current_event = ObjectEvent(protocol, summary_stats, game, event)
        logger.debug(f'Created new ObjectEvent at {event["_gameloop"]}')

    elif event['_event'] in ability_events:
        current_event = AbilityEvent(game, event)
        logger.debug(f'Created new AbilityEvent at {event["_gameloop"]}')

    elif event['_event'] == 'NNet.Game.SSelectionDeltaEvent':
        current_event = SelectionEvent(game, event)
        logger.debug(f'Created new SelectionEvent at {event["_gameloop"]}')

    elif event['_event'] == 'NNet.Game.SControlGroupUpdateEvent':
        current_event = ControlGroupEvent(game, event)
        logger.debug(f'Created new ControlGroupEvent at {event["_gameloop"]}')

    elif event['_event'] == 'NNet.Replay.Tracker.SUpgradeEvent':
        current_event = UpgradeEvent(game, event)
        logger.debug(f'Created new UpgradeEvent at {event["_gameloop"]}')

    elif event['_event'] == 'NNet.Game.SCameraUpdateEvent':
        current_event = CameraEvent(game, event)
        logger.debug(f'Created new CameraEvent at {event["_gameloop"]}')

    elif event['_event'] == 'NNet.Replay.Tracker.SPlayerStatsEvent':
        current_event = PlayerStatsEvent(summary_stats, game, event)
        logger.debug(f'Created new PlayerStatsEvent at {event["_gameloop"]}')

    else:
        current_event = None
        logger.warning(f'Event of type {event["_event"]} is not supported')

    return current_event
