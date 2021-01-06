from dataclasses import dataclass
from typing import Union, Literal, List, Dict, Optional

# used to explicitly show where the unit is gameloops
Gameloop = int
Resource = Union[Literal['minerals'], Literal['gas']]


@dataclass
class Map:
    """Contains the name and dimensions of the game map"""
    name: str
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass(frozen=True)
class Position:
    """Contains the x and y co-ordinates of a position"""
    x: float
    y: float


@dataclass(frozen=True)
class Upgrade:
    """Contains the name and completion time of an upgrade"""
    name: str
    completed_at: str


@dataclass(frozen=True)
class Ability:
    "Contains the name and energy cost of an ability"
    name: str
    energy_cost: Optional[int] = None


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
    """Contains generated unit, building, ability and upgrade data"""
    units: Dict[str, ObjectData]
    buildings: Dict[str, ObjectData]
    abilities: AbilityData
    upgrades: Dict[str, UpgradeData]
