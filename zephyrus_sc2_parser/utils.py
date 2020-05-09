import datetime
import math
import mpyq
import binascii
import requests
import struct
from io import BytesIO
from importlib import import_module
from zephyrus_sc2_parser.events import *
from zephyrus_sc2_parser.game.player import Player
import pytz
import logging


non_english_races = {
    b'\xed\x94\x84\xeb\xa1\x9c\xed\x86\xa0\xec\x8a\xa4': 'Protoss',
    b'\xe6\x98\x9f\xe7\x81\xb5': 'Protoss',
    b'\xe7\xa5\x9e\xe6\x97\x8f': 'Protoss',
    b'\xd0\x9f\xd1\x80\xd0\xbe\xd1\x82\xd0\xbe\xd1\x81\xd1\x81\xd1\x8b': 'Protoss',
    b'\xec\xa0\x80\xea\xb7\xb8': 'Zerg',
    b'\xe5\xbc\x82\xe8\x99\xab': 'Zerg',
    b'\xe8\x9f\xb2\xe6\x97\x8f': 'Zerg',
    b'\xed\x85\x8c\xeb\x9e\x80': 'Terran',
    b'\xe4\xba\xba\xe9\xa1\x9e': 'Terran',
    b'\xd0\xa2\xd0\xb5\xd1\x80\xd1\x80\xd0\xb0\xd0\xbd\xd1\x8b': 'Terran',
    b'\xe4\xba\xba\xe7\xb1\xbb': 'Terran'
}


def convert_time(windows_time):
    unix_epoch_time = math.floor(windows_time/10000000)-11644473600
    replay_datetime = datetime.datetime.fromtimestamp(unix_epoch_time).replace(tzinfo=pytz.utc)
    return replay_datetime


def create_players(player_info, events):
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
    if len(players) == 1:
        logging.info('Only one player in the game')
        # player_obj = min(players, key=lambda x: x.player_id)
        # player_obj.player_id = events[setup_index]['m_playerId']
        # player_obj.user_id = events[setup_index]['m_userId']
        return None

    # if both user_id's larger than 2 then lowest user_id first, the largest
    elif min(players) > 2:
        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']

        player_obj = max(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index+1]['m_playerId']
        player_obj.user_id = events[setup_index+1]['m_userId']

    # if both user_id's under 2 then the largest is set as 2 and the smallest is set as 1
    # specifically in that order to prevent assignment conflicts
    elif max(players) < 2:
        player_obj = max(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index+1]['m_playerId']
        player_obj.user_id = events[setup_index+1]['m_userId']

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
        player_obj.player_id = events[setup_index+1]['m_playerId']
        player_obj.user_id = events[setup_index+1]['m_userId']

    return players


def import_gamedata(protocol):
    protocol_name = protocol.__name__[8:]
    unit_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.unit_data')
    building_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.building_data')
    ability_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.ability_data')
    upgrade_data = import_module(f'zephyrus_sc2_parser.gamedata.{protocol_name}.upgrade_data')

    return {
        'units': unit_data.units,
        'buildings': building_data.buildings,
        'abilities': ability_data.abilities,
        'upgrades': upgrade_data.upgrades,
    }


def get_map_info(player_info, game_map):
    map_bytes = player_info['m_cacheHandles'][-1]
    server = map_bytes[4:8].decode('utf8').strip('\x00 ').lower()
    file_hash = binascii.b2a_hex(map_bytes[8:]).decode('utf8')
    file_type = map_bytes[0:4].decode('utf8')

    map_file = None
    for i in range(0, 5):
        map_response = requests.get(f'http://{server}.depot.battle.net:1119/{file_hash}.{file_type}')
        if map_response.status_code == 200:
            map_file = BytesIO(map_response.content)
            break
        logging.error(f'Could not fetch {game_map} map file. Retrying...')

    if not map_file:
        logging.critical(f'Failed to fetch {game_map} map file')
        return None

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

    return {
        'name': game_map,
        'width': map_width,
        'height': map_height,
    }


def create_event(game, event, protocol, summary_stats):
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

    elif event['_event'] in ability_events:
        current_event = AbilityEvent(summary_stats, game, event)

    elif event['_event'] == 'NNet.Game.SSelectionDeltaEvent':
        current_event = SelectionEvent(game, event)

    elif event['_event'] == 'NNet.Game.SControlGroupUpdateEvent':
        current_event = ControlGroupEvent(game, event)

    elif event['_event'] == 'NNet.Replay.Tracker.SUpgradeEvent':
        current_event = UpgradeEvent(game, event)

    elif event['_event'] == 'NNet.Game.SCameraUpdateEvent':
        current_event = CameraUpdateEvent(game, event)

    elif event['_event'] == 'NNet.Replay.Tracker.SPlayerStatsEvent':
        current_event = PlayerStatsEvent(summary_stats, game, event)

    else:
        current_event = None

    return current_event
