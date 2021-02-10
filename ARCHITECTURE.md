# Architecture

This document describes the general structure of the parser and how different areas of the codebase interact with one another.

## Overview

The goal of the parser is to generate useful game data and perform high level analysis. It's supposed to make it easy for users to extract useful data from replays.

It achieves this by processing game events and building up the state of the game from event data. Game state is recorded in a few core data structures (Game, GameObj, Player), which are all mutable.

Some data is lost throughout the parsing process due to mutability, however snapshots of the current game state are recorded at regular intervals (This is the timeline). Other data is recorded in the core data structures (I.e. player selections).

There is also some secondary parsing after all game events have been processed, which involves re-processing data for high level analysis.

## Initial Setup

- What needs to happen before we start processing events?
    - Need to parse file
    - Need to access appropriate data
    - Need to setup core data structures

## Parsing Loop

To re-create the game state, we iterate through all the game events and mutate the current state accordingly. This parsing loop is a core part of the parser and is found in `zephyrus_sc2_parser/parser.py`. 

Here's a basic description of what happens when an event is processed:

```
1. Create event object
2. Extract relevant data from the event
3. Mutate game state with updated data
```

Notes:

- If an event is not supported by the parser, it's skipped and no event object is created
- Event objects are like classes of events. Multiple different events can correspond to the same type of event object
- In general, the parsing loop should be as pure as possible. The exceptions to this are mutations that span multiple events and global mutations

## Events

Notes:

- All events inherit from `BaseEvent`
- All events implement the `parse_event` method. This is the only public method events implement
- All events are strictly self-contained. They should **NOT** be mutated from outside the event object itself
- In general, events are the only place where mutation of core data structures (GameObj, Player) should occur. The exceptions to this are mutations during initial setup and in the parsing loop
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

These are all directly related to mutations of in-game objects (i.e. `GameObj`s).

Since this event is related to `GameObj`s, it attempts to find the `GameObj` and `Player` related to the event. If either of these lookups fail, the event is aborted.

If the lookup succeeds, the `GameObj` is mutated based on the data in the event.

### `SelectionEvent`

A `SelectionEvent` is only related to the `NNet.Game.SSelectionDeltaEvent` game event. However, this event is quite complex.

This event manages all mutations related to player selections. Units being box selected, units being shift deselected, units dying while being selected, units spawning from selected Eggs, etc. (This applies to buildings as well of course).

### `ControlGroupEvent`

A `SelectionEvent` is only related to the `NNet.Game.SSelectionDeltaEvent` game event. However, this event is quite complex.

This event is related to the `SelectionEvent` event, but there is no overlap in functionality. 

### `AbilityEvent`

An `AbilityEvent` spans two game events:

- `NNet.Game.SSelectionDeltaEvent`
- `NNet.Game.SSelectionDeltaEvent`.

This event relates to abilities used by `GameObj`s.

When a xxxx game event occurs, it is effectively cached for that player. If the same event is repeated multiple times, an yyyy event fires instead of a xxxx event.

yyyy events have limited information, so we track information about which ability is currently active for each player.

### `PlayerStatsEvent`

A `PlayerStatsEvent` is only related to the `NNet.Game.SSelectionDeltaEvent` game event. However, this event is quite complex.

### `UpgradeEvent`

A `UpgradeEvent` is only related to the `NNet.Game.SSelectionDeltaEvent` game event. However, this event is quite complex.

### `CameraEvent`

A `CameraEvent` is only related to the `NNet.Game.SSelectionDeltaEvent` game event. However, this event is quite complex.

### `PlayerLeaveEvent`

A `PlayerLeaveEvent` is only related to the `NNet.Game.SPlayerLeaveEvent` game event. However, this event is quite complex.
