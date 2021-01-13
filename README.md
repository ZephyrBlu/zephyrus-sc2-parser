# Zephyrus Replay Parser

A robust and detailed parser for .SC2Replay files. Only 1v1 games are currently supported.

Used by [zephyrus.gg](https://zephyrus.gg) for in-depth replay analysis.

## Core Features

- **Easy to use**

  No need to configure anything, just install the package and call `parse_replay`

- **Battle Tested**

  The parser is used on [zephyrus.gg](https://zephyrus.gg) and has been used to process over 70k replays with very few failing. For common failure modes there are also custom exceptions to make it clear why parsing failed.

- **Stateful and Object Orientated**

  Core game elements are recreated with objects (Game, GameObj, Player, PlayerState) allowing for an easy understanding of where information is located and how it is interlinked.
  Events and information are re-calculated on every relevant event, so you always have the correct gamestate.
  Gamestate is recorded at regular intervals (5sec) to allow easy analysis on parsed information.
  Raw data is available through all main objects (Game.events, GameObj.birth_time, Player.objects, etc).

- **Extremely Detailed Information**

  The parser utilizes both the tracker and game events from replay files to re-create gamestate, allowing much more complex information to be gathered.

  Ex:
   - Unit Modes: Warp Prism Flying vs Phasing
   - Creep: Active Tumors, Dead Tumors, Total Creep Tiles
   - Ability Attribution/Energy Tracking (Command Structures only)
   - Selection/Control Group Tracking

## Installation and Usage

The parser is hosted on PyPI. You can install it through pip

`pip install zephyrus_sc2_parser`

You can import `parse_replay` as a top level import

`from zephyrus_sc2_parser import parse_replay`

### Required Arguments

The only required argument is the path of the replay you want to parse

### Optional Keyword Arguments

You can optionally use the `local` flag to indicate you want to parse a replay without MMR, otherwise the parser will abort the replay. `local` is set to False by default.

By default the generated timeline will be in 5sec intervals (22.4 gameloops = 1 second, 22.4 * 5 = 112). You can specify a custom interval in gameloops using the `tick` keyword argument.

The `network` flag can be used to disable network requests, since maps that aren't cached in `zephyrus_sc2_parser/gamedata/map_info.py` require one to get the map size (Used for Creep calculations). `network` is set to True by default.

### Return Values

The parser returns a [named tuple](https://docs.python.org/3/library/collections.html#collections.namedtuple) which can either be handled like a single object, or spread into distinct values.

The data returned is:
- Dictionary containing both player objects
- List of recorded game states
- List of recorded engagements
- Dictionary of summary stats containing general information about both players
- Dictionary of metadata about the game

Currently engagements is empty, but it will contain engagement data in the future.

### Examples

```
# data can be accessed with dot notation
# replay.players, replay.timeline, replay.engagements, replay.summary, replay.metadata
replay = parse_replay(filepath, local=False, tick=112, network=True)

OR

# you can name these however you like
players, timeline, engagements, summary, metadata = parse_replay(filepath, local=False, tick=112, network=True)
```

Example of `players`:

    {
      1: <Player object>, # see zephyrus_sc2_parser/game/player.py for details
      2: <Player object>,
    }
    
Example of `timeline`:
    
    # one gamestate, not actual data
    # see zephyrus_sc2_parser/game/player_state.py for details
    [{
        1: {
            'gameloop': 3000,
            'resource_collection_rate': { 'minerals': 1200, 'gas': 800 },
            'unspent_resources': { 'minerals': 300, 'gas': 400 },
            'resource_collection_rate_all': 2000,
            'unit': {
                'Probe': {
                    'type': ['unit', 'worker'],
                    'live': 50,
                    'died': 15,
                    'in_progress': 0,
                    'mineral_cost': 50,
                    'gas_cost': 0,
                },
                'Stalker': {
                    'type': ['unit'],
                    'live': 12,
                    'died': 0,
                    'in_progress': 0,
                    'mineral_cost': 125,
                    'gas_cost': 50,
                },
            },
            'building': {
                'CyberneticsCore': {
                    'type': ['building'],
                    'live': 1,
                    'died': 0,
                    'in_progress': 0,
                    'mineral_cost': 150,
                    'gas_cost': 0,
                },
                'ShieldBattery': {
                    'type': ['building'],
                    'live': 2,
                    'died': 0,
                    'in_progress': 0,
                    'mineral_cost': 100,
                    'gas_cost': 0,
                }
            },
            'upgrade': [],
            'current_selection': { 'Stalker': 2 },
            'workers_active': 50,
            'workers_produced': 38,
            'workers_lost': 0,
            'supply': 74,
            'supply_cap': 100,
            'supply_block': 0,
            'spm': 0,
            'army_value': { 'minerals': 1500, 'gas': 600 },
            'resources_lost': { 'minerals': 750, 'gas': 0 },
            'resources_collected': { 'minerals': 10500, 'gas': 2500 },
            'total_army_value': 2100,
            'total_resources_lost': 0,
            'total_resources_collected': 13000,
            'race': {},
        },
        2: {
            ...
        },
    }]
    
Example of `summary`:

    # not actual data
    {
        'mmr': { 1: 3958, 2: 3893 },
        'avg_resource_collection_rate': {
            'minerals': { 1: 1150.9, 2: 1238.6 },
            'gas': { 1: 321.7, 2: 316.8 }
        },
        'max_collection_rate': { 1: 2400, 2: 2200 },
        'avg_unspent_resources': {
            'minerals': { 1: 330.7, 2: 247.3 },
            'gas': { 1: 205.2, 2: 174.5 }
        },
        'apm': { 1: 123.0, 2: 187.0 },
        'spm': { 1: 7, 2: 10.4 },
        'resources_lost': {
            'minerals': { 1: 2375, 2: 800 },
            'gas': { 1: 1000, 2: 425 } 
        },
        'resources_collected': {
            'minerals': { 1: 22000, 2: 23000 },
            'gas': { 1: 5400, 2: 7500 } 
        },
        'workers_produced': { 1: 63, 2: 48 },
        'workers_killed': { 1: 12, 2: 41 },
        'workers_lost': { 1: 41, 2: 12 },
        'supply_block': { 1: 20, 2: 5 },
        'sq': { 1: 91, 2: 104 },
        'avg_pac_per_min': { 1: 28.15, 2: 36.29 },
        'avg_pac_action_latency': { 1: 0.46, 2: 0.32 },
        'avg_pac_actions': { 1: 3.79, 2: 4.65 },
        'avg_pac_gap': { 1: 0.37, 2: 0.25 },
        'race': { 1: {}, 2: {} },
    }

Example of `metadata`:

    # not actual data
    {
        'map': 'Acropolis LE',
        
        # UTC timezone
        'played_at': <datetime.datetime object>,
        
        # player ID
        'winner': 1,
        
        # seconds
        'game_length': 750,
    }
