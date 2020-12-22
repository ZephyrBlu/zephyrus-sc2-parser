from dataclasses import dataclass
from typing import Any, Union, List, Dict, Literal, Optional, NamedTuple
from zephyrus_sc2_parser.game import Player, GameObj


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
    players: Player
    timeline: List[GameState]
    engagements: List
    summary: Union[SummaryStat, Dict[str, SummaryStat]]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class Map:
    width: int
    height: int


@dataclass(frozen=True)
class Position:
    x: float
    y: float


@dataclass(frozen=True)
class Upgrade:
    name: str
    completed_at: str


@dataclass(frozen=True)
class Ability:
    name: str
    energy_cost: Optional[int] = None


@dataclass(frozen=True)
class ActiveAbility:
    ability: Ability
    obj: Optional[GameObj]
    target_position: Optional[Position]
    queued: Literal


# ObjectData = {
#     <obj name>: {
#         <property name>: <property value>
#     }
# }
ObjectData = Dict[str, Dict[str, Union[int, List[str]]]]

# AbilityData = {
#     <ability id>: {
#         ability_name: <ability name>
#         AND MAYBE
#         energy_cost: <energy cost>
#     }
# }
AbilityData = Dict[int, Dict[str, Union[str, int]]]

# UpgradeData = {
#     <upgrade name>: {
#         mineral_cost: <mineral cost>,
#         gas_cost: <gas cost>,
#     }
# }
UpgradeData = Dict[str, Dict[str, int]]


@dataclass(frozen=True)
class GameData:
    units: Dict[str, ObjectData]
    buildings: Dict[str, ObjectData]
    abilities: AbilityData
    upgrades: Dict[str, UpgradeData]
