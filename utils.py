import datetime
import math
from zephyrus_sc2_parser.events import (
    ObjectEvent, AbilityEvent, SelectionEvent, ControlGroupEvent,
    UpgradeEvent, CameraUpdateEvent, PlayerStatsEvent
)
from zephyrus_sc2_parser.game.player import Player


def convert_time(windows_time):
    unix_epoch_time = math.floor(windows_time/10000000)-11644473600
    replay_datetime = datetime.datetime.fromtimestamp(unix_epoch_time).strftime('%Y-%m-%d %H:%M:%S')
    return replay_datetime


def create_players(player_info, events):
    # get player name and race
    # workingSetSlotId correlates to playerIDs
    players = []

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

    # first 2 events in every replay with 2 players is always setup for playerIDs
    # need to look at the setup to match player IDs to players
    setup_index = 0
    for setup_index, event in enumerate(events):
        if event['_event'] == 'NNet.Replay.Tracker.SPlayerSetupEvent':
            break

    # logic for translating user_id's into playerID's

    # if only one player then playerID is always 0
    if len(players) == 1:
        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']
    else:
        player_obj = min(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']

        player_obj = max(players, key=lambda x: x.player_id)
        player_obj.player_id = events[setup_index+1]['m_playerId']
        player_obj.user_id = events[setup_index+1]['m_userId']

    return players


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
