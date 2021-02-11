# Architecture

This document describes the general structure of the parser and how different areas of the codebase interact with one another.

## Overview

The goal of the parser is to generate useful game data and perform high level analysis. It's supposed to make it easy for users to extract useful data from replays.

It achieves this by processing game events and building up the state of the game from event data. Game state is recorded in a few core data structures (`Game`, `GameObj`, `Player`), which are all mutable.

Some data is lost throughout the parsing process due to mutability, however snapshots of the current game state are recorded at regular intervals (This is the timeline). Other data is recorded in the core data structures (I.e. player selections).

There is also some secondary parsing after all game events have been processed, which involves re-processing data for high level analysis.

## Data Structures

There are 2 extremely commmon data structures used in the parser: `GameObj` and `Player`. They are both found in the `zephyrus_sc2_parser/game` folder.

`GameObj` objects contain the current state of units and buildings as well as underlying information such as mineral cost, type (Worker, building, unit or supply), etc.

`Player` objects contain the current state of things under a player's control (Control Groups, Units/Buildings, etc) as well as a lot of historical data (Resource Collection rates, Selections, etc). 

## Initial Setup

Before we can starting processing game events, we need to parse the replay file itself and set up a few data structures and populate them with basic information.

Most of this occurs in the `_setup` function in `zephyrus_sc2_parser/parser.py`.

The most important thing that occurs during the initial setup is populating `Player` objects with their ids. Some events have user ids, and some have player ids. User ids are matched up with player ids in the `_create_players` function in `zephyrus_sc2_parser/utils.py`.

## Parsing Loop

To re-create the game state, we iterate through all the game events and mutate the current state accordingly. This parsing loop is a core part of the parser and is found in `zephyrus_sc2_parser/parser.py`. 

Here's a basic description of what happens when an event is processed:

1. Create event object
2. Extract relevant data from the event
3. Mutate game state with updated data

Notes:

- If an event is not supported by the parser, it's skipped and no event object is created
- Event objects are like classes of events. Multiple different events can correspond to the same type of event object
- In general, the parsing loop should be as pure as possible. The exceptions to this are mutations that span multiple events and global mutations

## Events

Notes:

- All events only relate to one (1) player
- All events inherit from `BaseEvent`
- All events implement the `parse_event` method. This is the only public method events implement
- All events are strictly self-contained. They should **NOT** be mutated from outside the event object itself
- In general, events are the only place where mutation of core data structures (`GameObj`, `Player`) should occur. The exceptions to this are mutations during initial setup and in the parsing loop
- You should think of events as the main method of communication between data structures like so:

`GameObj/Player <--> event <--> GameObj/Player`

### `BaseEvent`

The `BaseEvent` populates the event object with some basic generic data about the event. Any non-generic data is extracted in the specific event.

### `ObjectEvent`

An `ObjectEvent` spans 5 different game events:

- `NNet.Replay.Tracker.SUnitInitEvent`
- `NNet.Replay.Tracker.SUnitDoneEvent`
- `NNet.Replay.Tracker.SUnitBornEvent`
- `NNet.Replay.Tracker.SUnitDiedEvent`
- `NNet.Replay.Tracker.SUnitTypeChangeEvent`

These are all directly related to mutations of in-game objects (i.e. `GameObj` objects).

Since this event is related to `GameObj` objects, it attempts to find the `GameObj` and `Player` related to the event. If either of these lookups fail, the event is aborted.

If the lookup succeeds, the `GameObj` is mutated based on the data in the event.

### `SelectionEvent`

A `SelectionEvent` is related to the `NNet.Game.SSelectionDeltaEvent` game event. However, the domain knowledge and logic required to handle this event is quite complex.

This event manages all mutations related to player selections. Units being box selected, units being shift deselected, units dying while being selected, units spawning from selected Eggs, etc. (This applies to buildings as well of course).

### `ControlGroupEvent`

A `ControlGroupEvent` is related to the `NNet.Game.SControlGroupUpdateEvent` game event. However, the domain knowledge and logic required to handle this event is quite complex.

This event is related to the `SelectionEvent` event, but there is no overlap in functionality. 

### `AbilityEvent`

An `AbilityEvent` spans two game events:

- `NNet.Game.SCmdEvent`
- `NNet.Game.SCommandManagerStateEvent`

This event relates to abilities used by `GameObj` objects.

When a `NNet.Game.SCmdEvent` game event occurs, it is effectively cached for that player. If the same event is repeated multiple times, a `NNet.Game.SCommandManagerStateEvent` event fires instead of a `NNet.Game.SCmdEvent` event.

`NNet.Game.SCommandManagerStateEvent` events have limited information, so we track information about which ability is currently active for each player.

### `PlayerStatsEvent`

A `PlayerStatsEvent` is related to the `NNet.Replay.Tracker.SPlayerStatsEvent` game event.

This event occurs every 160 gameloops (\~7 seconds) and contains a lot of information which otherwise can't easily be obtained such as current values for Supply, Unspent Resources, Resources in Queue, etc.

### `UpgradeEvent`

An `UpgradeEvent` is related to the `NNet.Replay.Tracker.SUpgradeEvent` game event.

This event occurs when an upgrade completes. Some upgrade names are not immediately intuitive as they are old names.

### `CameraEvent`

A `CameraEvent` is related to the `NNet.Game.SCameraUpdateEvent` game event.

This event occurs every time the camera position, pitch, roll or yaw changes.

### `PlayerLeaveEvent`

A `PlayerLeaveEvent` is related to the `NNet.Game.SPlayerLeaveEvent` game event.

This event occurs when a player or observer leaves the game.
