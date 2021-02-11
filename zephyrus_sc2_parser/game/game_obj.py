import math
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Union, Literal, Deque
from zephyrus_sc2_parser.dataclasses import Gameloop, Ability, Position


@dataclass(frozen=True)
class UnitName:
    name: str
    gameloop: Gameloop


class GameObj:
    """
    Contains detailed information about a game object (Unit or building),
    plus a few related methods
    """
    # obj statuses
    LIVE = 'LIVE'
    DIED = 'DIED'
    IN_PROGRESS = 'IN_PROGRESS'

    # obj types
    UNIT = 'UNIT'
    BUILDING = 'BUILDING'
    WORKER = 'WORKER'
    SUPPLY = 'SUPPLY'

    def __init__(
        self,
        name: str,
        obj_id: int,
        game_id: int,
        tag: int,
        recycle: int,
        priority: int,
        mineral_cost: int,
        gas_cost: int,
    ):
        self.name: str = name
        self._name_history: List[UnitName] = [UnitName(self.name, 0)]

        GameObjType = Union[
            Literal[self.UNIT],
            Literal[self.BUILDING],
            Literal[self.WORKER],
            Literal[self.SUPPLY],
        ]
        self.type: List[GameObjType] = []

        self.obj_id: int = obj_id
        self.game_id: int = game_id
        self.tag: int = tag
        self.recycle: int = recycle
        self.priority: int = priority
        self.mineral_cost: int = mineral_cost
        self.gas_cost: int = gas_cost
        self.energy: Optional[float] = None
        self.supply: int = 0
        self.supply_provided: int = 0
        self.cooldown: Optional[int] = None

        # currently unused
        self.queue: Optional[Deque[GameObj]] = None

        # for Zerg, _created_units holds Larva for injects
        self._created_units: Optional[List[GameObj]] = None
        self.control_groups: Dict[int, int] = {}
        self.abilities_used: List[Tuple[Ability, GameObj, Gameloop]] = []
        self.energy_efficiency: Optional[Tuple[float, float]] = None
        self.init_time: Optional[Gameloop] = None
        self.birth_time: Optional[Gameloop] = None
        self.death_time: Optional[Gameloop] = None
        self.morph_time: Optional[Gameloop] = None
        self.position: Optional[Position] = None

        # currently unused (I think)
        self.target: None = None

        GameObjStatus = Union[
            Literal[self.LIVE],
            Literal[self.DIED],
            Literal[self.IN_PROGRESS],
        ]
        self.status: GameObjStatus = None

        self.killed_by: Optional[GameObj] = None

    def __eq__(self, other):
        return self.game_id == other.game_id

    def __hash__(self):
        return hash(self.game_id)

    def __repr__(self):
        return f'({self.name}, {self.tag})'

    def update_name(self, new_name: str, gameloop: Gameloop):
        self.name = new_name
        self._name_history.append(UnitName(new_name, gameloop))

    def name_at_gameloop(self, gameloop: Gameloop) -> str:
        current_name = None
        for obj_name in self._name_history:
            if gameloop >= obj_name.gameloop:
                current_name = obj_name.name
            # if current gameloop is less than the obj name gameloop
            # we haven't reached that gameloop yet, so can exit
            else:
                break

        return current_name

    def calc_distance(self, other_position: Position) -> Optional[float]:
        if not self.position:
            return None

        # position contains x, y, z in integer form of floats
        # simple pythagoras theorem calculation
        x_diff = abs(self.position.x - other_position.x)
        y_diff = abs(self.position.y - other_position.y)
        distance = math.sqrt(x_diff ** 2 + y_diff ** 2)
        return distance

    def calc_energy(self, gameloop: Gameloop) -> Optional[float]:
        # need to check for int since 0 is falsy
        if not self.energy or (not self.morph_time and type(self.birth_time) != int):
            return None

        # regen per gameloop
        energy_regen_rate = 0.03515625
        max_energy = 200

        def energy_maxout(current_gameloop, current_energy, target_energy):
            return int(round(current_gameloop + ((target_energy - current_energy) / energy_regen_rate), 0))

        # morph time for Orbitals
        initial_gameloop = self.morph_time or self.birth_time
        current_gameloop = initial_gameloop
        current_energy = self.energy
        time_past_min_energy = 0

        for ability, ability_target, ability_gameloop in self.abilities_used:
            if not ability.energy_cost:
                continue

            # only want to measure efficiency of command structures
            if 'building' in self.type:
                min_usable_energy_gameloop = energy_maxout(current_gameloop, current_energy, 50)
                if ability_gameloop >= min_usable_energy_gameloop:
                    if min_usable_energy_gameloop <= current_gameloop:
                        time_past_min_energy += ability_gameloop - current_gameloop
                    else:
                        time_past_min_energy += ability_gameloop - min_usable_energy_gameloop

            if ability_gameloop >= energy_maxout(current_gameloop, current_energy, max_energy):
                current_energy = 200
            else:
                current_energy += energy_regen_rate * (ability_gameloop - current_gameloop)
            current_gameloop = ability_gameloop
            current_energy -= ability.energy_cost

        if 'building' in self.type:
            min_usable_energy_gameloop = energy_maxout(current_gameloop, current_energy, 50)
            if min_usable_energy_gameloop <= gameloop:
                if min_usable_energy_gameloop < current_gameloop:
                    time_past_min_energy += gameloop - current_gameloop
                else:
                    time_past_min_energy += gameloop - min_usable_energy_gameloop
                try:
                    self.energy_efficiency = (round(1 - (time_past_min_energy / gameloop), 3), round(time_past_min_energy / 22.4, 1))
                except ZeroDivisionError:
                    self.energy_efficiency = (1.0, round(time_past_min_energy / 22.4, 1))

        if gameloop >= energy_maxout(current_gameloop, current_energy, max_energy):
            current_energy = max_energy
        else:
            current_energy += energy_regen_rate * (gameloop - current_gameloop)

        return round(current_energy, 1)

    def calc_inject_efficiency(self, gameloop: Gameloop) -> Optional[Tuple[float, int]]:
        if not self.abilities_used or self.name not in ['Hatchery', 'Lair', 'Hive']:
            return None

        # only 1 inject = 100% efficiency
        if len(self.abilities_used) == 1:
            return (1.0, 1)

        # ~29sec
        inject_delay = 650

        missed_inject_time = 0
        current_gameloop = self.abilities_used[0][-1]
        for i in range(1, len(self.abilities_used)):
            current_inject = self.abilities_used[i]

            time_diff = current_inject[-1] - current_gameloop - inject_delay

            # time diff < 0, inject was queued, 100% efficiency
            if time_diff > 0:
                missed_inject_time += time_diff
                current_gameloop = current_inject[-1]
            else:
                current_gameloop = current_inject[-1] + inject_delay

        inject_efficiency = 1 - (missed_inject_time / (current_gameloop - self.abilities_used[0][-1] + inject_delay))

        return (round(inject_efficiency, 3), missed_inject_time)
