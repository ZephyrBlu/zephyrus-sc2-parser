# Zephyrus Replay Parser

A robust and detailed parser for .SC2Replay files

Used by [zephyrus.gg](https://zephyrus.gg) for in-depth replay analysis

Detailed documentation coming soon!

## Core Features

- **Easy to use**

  No need to configure anything, just install the package and call `parse_replay` to get started

- **Stateful and Object Orientated**

  Core game elements are recreated with objects allowing for an easy understanding of where information is located and how it is interlinked.
  Events and information are recalculated on every relevant event, so you always have the correct gamestate.
  Gamestate is also recorded at regular intervals to allow easy analysis on parsed information

- **Extremely Detailed Information**

  The parser utilizes both the tracker and game events from replay files to re-create gamestate, allowing much more complex information to be gathered.
  Game IDs for units, buildings and abilities have painstakingly found and recorded to allow information such as unit and building modes,
  ability usage and creation status to be parsed
  
- **Accurate Selection Tracking**

  Previous parsers either did not track player selections or had inaccurate implementations. Our implementation accurately tracks player
  selections even during complex subselection and deselection actions thanks to a robust bitmask algorithm


## Installation and Usage

The parser is hosted on PyPI. You can install it through pip

`pip install zephyrus_sc2_parser`

`parse_replay` is imported by default but you can import it manually for specificity if you want

`import zephyrus_sc2_parser` or `from zephyrus_sc2_parser import parse_replay`

You must pass in the path to the replay file you want to parse. You can optionally use the `local` flag to indicate
you want to parse a replay without MMR, otherwise the parser will abort the replay. `local` is set to False by default.

The parser returns 4 values, a dictionary containing both player objects, a list of recorded game states, a dictionary of summary stats containing
general information about both players and a dictionary of metadata about the game.

`players, timeline, summary_stats, metadata = parse_replay(filepath, local=False)`

Example of `players`:

    {
      1: <Player object>,
      2: <Player object>,
    }
    
Example of `timeline`:
    
    # one gamestate
    [{
        1: {
            'gameloop': 3000,
            'resource_collection_rate': { 'minerals': 1200, 'gas': 800 },
            'unspent_resources': { 'minerals': 300, 'gas': 400 },
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
            'current_selection': { 'Stalker': 2 },
            'workers_active': 50,
            'workers_killed': 0,
            'army_value': { 'minerals': 1500, 'gas': 600 },
            'resources_lost': { 'minerals': 750, 'gas': 0 },
            'total_army_value': 2100,
            'total_resources_lost': 0,
        },
        2: {
            ...
        },
    }]
    
Example of `summary_stats`:

    {
        'mmr': { 1: 3958, 2: 3893 },
        'mmr_diff': { 1: 65, 2: -65 },
        'avg_resource_collection_rate': {
            'minerals': { 1: 1150.9, 2: 1238.6 },
            'gas': { 1: 321.7, 2: 316.8 }
        },
        'avg_unspent_resources': {
            'minerals': { 1: 330.7, 2: 247.3 },
            'gas': { 1: 205.2, 2: 174.5 }
        },
        'apm': { 1: 123.0, 2: 187.0 },
        'resources_lost': {
            'minerals': { 1: 2375, 2: 800 },
            'gas': { 1: 1000, 2: 425 } 
        },
        'workers_produced': { 1: 63, 2: 48 },
        'workers_killed': { 1: 12, 2: 41 },
        'workers_lost': { 1: 41, 2: 12 },
        'inject_count': { 1: 0, 2: 0 },
        'sq': { 1: 91, 2: 104 },
        'avg_pac_per_min': { 1: 28.15, 2: 36.29 },
        'avg_pac_action_latency': { 1: 0.46, 2: 0.32 },
        'avg_pac_actions': { 1: 3.79, 2: 4.65 },
        'avg_pac_gap': { 1: 0.37, 2: 0.25 },
    }

Example of `metadata`:

    {
        'map': 'Acropolis LE',
        
        # UTC timezone
        'time_played_at': <datetime.datetime object>,
        
        # player ID
        'winner': 1,
        
        # seconds
        'game_length': 750,
    }
