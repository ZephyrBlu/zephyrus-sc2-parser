import math
from dataclasses import dataclass
from typing import Union, Literal, Optional, Dict, List, Set, Tuple, AnyStr
from zephyrus_sc2_parser.dataclasses import (
    Gameloop,
    Resource,
    Ability,
    Upgrade,
    Position,
    Map,
)
from zephyrus_sc2_parser.game.game_obj import GameObj

# these are here instead of in dataclasses.py
# to prevent circular imports
@dataclass
class Selection:
    """Contains the objects in, and the start/end time of, a selection"""
    objects: List[GameObj]
    start: Gameloop
    end: Optional[Gameloop]


@dataclass(frozen=True)
class ActiveAbility:
    """
    Contains the ability, target object and target position
    of a player's currently active ability
    """
    ability: Ability
    obj: Optional[GameObj]
    target_position: Optional[Position]
    queued: bool


Race = Union[
    Literal['Protoss'],
    Literal['Terran'],
    Literal['Zerg'],
]


class Player:
    """Contains detailed information about a player, plus a few related methods"""
    def __init__(
        self,
        player_id: int,
        profile_id: int,
        region_id: int,
        realm_id: int,
        name: AnyStr,
        race: AnyStr,
    ):
        self.player_id: int = player_id

        if type(name) is bytes:
            formatted_name = name.decode('utf-8').split('>')[-1]
        else:
            formatted_name = name.split('>')[-1]
        self.name: str = formatted_name

        if type(race) is bytes:
            formatted_race = race.decode('utf-8')
        else:
            formatted_race = race
        self.race: Race = formatted_race

        self.user_id: Optional[int] = None
        self.profile_id: int = profile_id
        self.region_id: int = region_id
        self.realm_id: int = realm_id
        self.objects: Dict[int, GameObj] = {}
        self.upgrades: List[Upgrade] = []
        self.current_selection: List[GameObj] = []
        self.control_groups: Dict[int, List[GameObj]] = {}
        self.selections: List[Selection] = []

        # currently unused (I think)
        self.warpgate_cooldowns = []
        self.warpgate_efficiency = (0, 0)

        self.active_ability: Optional[ActiveAbility] = None

        # PAC related. Unsure of types right now
        self.pac_list = []
        self.current_pac = None
        self.prev_screen_position = None
        self.screens = []

        self.supply: int = 0
        self.supply_cap: int = 0
        self.supply_block: int = 0
        self._supply_blocks: List = []
        self.queues: List = []
        self.idle_larva: List[int] = []
        self._creep_tiles: Optional[Set[Position]] = None
        self.army_value: Dict[Resource, List[int]] = {
            'minerals': [],
            'gas': [],
        }
        self.unspent_resources: Dict[Resource, List[int]] = {
            'minerals': [],
            'gas': [],
        }
        self.collection_rate: Dict[Resource, List[int]] = {
            'minerals': [],
            'gas': [],
        }
        self.resources_collected: Dict[Resource, int] = {
            'minerals': 0,
            'gas': 0,
        }

    def __lt__(self, other):
        return self.player_id < other

    def __le__(self, other):
        return self.player_id <= other

    def __eq__(self, other):
        return self.player_id == other

    def __ge__(self, other):
        return self.player_id >= other

    def __gt__(self, other):
        return self.player_id > other

    def __ne__(self, other):
        return not self.player_id == other

    # def calc_supply(self):
    #     total_supply = 0
    #     total_supply_provided = 0

    #     for obj_id, obj in self.objects.items():
    #         if obj.status == 'live' or ('Overlord' not in obj.name and obj.status == 'in_progress' and 'unit' in obj.type):
    #             total_supply += obj.supply
    #             total_supply_provided += obj.supply_provided

    #     self.supply = total_supply
    #     self.supply_cap = total_supply_provided

    def to_json(self) -> Dict[str, Union[str, int]]:
        return {
            'name': self.name,
            'race': self.race,
            'player_id': self.player_id,
            'realm_id': self.realm_id,
            'region_id': self.region_id,
            'profile_id': self.profile_id,
        }

    def calc_spm(self, gameloop: Gameloop, *, recent=False) -> Union[float, int]:
        if not recent:
            try:
                return round(len(self.screens) / (gameloop / 22.4 / 60), 1)
            except ZeroDivisionError:
                return 0

        # 1 minute in gameloops
        gameloop_minute = 1344
        prev_minute_screens = 0

        for screen_gameloop in self.screens:
            if screen_gameloop >= gameloop - gameloop_minute:
                prev_minute_screens += 1

        return prev_minute_screens

    def calc_creep(self, game_map: Map) -> Tuple[Tuple[float, int], int, int]:
        if self.race != 'Zerg' or not (game_map.width and game_map.height):
            return None, None, None

        if not self._creep_tiles:
            self._creep_tiles = set()

        creep_tumor_count = 0
        creep_tumors_died = 0
        for obj in self.objects.values():
            # odd tile objects position += 0.5. Rounded off in events
            if obj.name == 'Hatchery' or obj.name == 'Lair' or obj.name == 'Hive':
                creep_radius = 12
            elif obj.name == 'CreepTumorBurrowed':
                creep_radius = 10

                if obj.status == GameObj.LIVE:
                    creep_tumor_count += 1
                elif obj.status == GameObj.DIED:
                    creep_tumors_died += 1
            else:
                continue

            # add 0.5 to get center of central tile
            building_position = (obj.position.x + 0.5, obj.position.y + 0.5)

            if obj.status == GameObj.DIED:
                def remove_tiles(tile_range, current_position):
                    # always add midpoint in row
                    try:
                        self._creep_tiles.remove(current_position)
                    except KeyError:
                        pass

                    # if only 1 tile in row, we're done
                    # else expand horizontally, count new tiles until max radius
                    # this should never happen with the improved approximation
                    if tile_range != 0:
                        for j in range(0, tile_range + 1):
                            try:
                                self._creep_tiles.remove((current_position[0] + j, current_position[1]))
                                self._creep_tiles.remove((current_position[0] - j, current_position[1]))
                            except KeyError:
                                continue

                # removing middle row tiles
                remove_tiles(creep_radius, building_position)

                for i in range(0, creep_radius // 2):
                    row_increment = i + 1

                    # ----- full-size rows -----
                    # add radius/2 full-size rows to improve area approximation
                    remove_tiles(
                        creep_radius,
                        (
                            building_position[0],
                            building_position[1] + row_increment,
                        ),
                    )

                    # tile actions are mirrored in y-axis
                    remove_tiles(
                        creep_radius,
                        (
                            building_position[0],
                            building_position[1] - row_increment,
                        ),
                    )

                    # ----- decreasing size rows -----
                    remove_tiles(
                        creep_radius - row_increment,
                        (
                            building_position[0],
                            building_position[1] + row_increment + creep_radius / 2,
                        ),
                    )

                    # tile actions are mirrored in y-axis
                    remove_tiles(
                        creep_radius - row_increment,
                        (
                            building_position[0],
                            building_position[1] - row_increment - creep_radius / 2,
                        ),
                    )
                continue

            elif obj.status != GameObj.LIVE:
                continue

            def add_tiles(tile_range, current_position):
                # always add midpoint in row
                self._creep_tiles.add(current_position)

                # if only 1 tile in row, we're done
                # else expand horizontally, count new tiles until max radius
                # this should never happen with the improved approximation
                if tile_range != 0:
                    for j in range(0, tile_range + 1):
                        self._creep_tiles.add((current_position[0] + j, current_position[1]))
                        self._creep_tiles.add((current_position[0] - j, current_position[1]))

            # adding middle row tiles
            add_tiles(creep_radius, building_position)

            for i in range(0, creep_radius // 2):
                row_increment = i + 1

                # ----- full-size rows -----
                # add radius/2 full-size rows to improve area approximation
                add_tiles(
                    creep_radius,
                    (
                        building_position[0],
                        building_position[1] + row_increment,
                    ),
                )

                # tile actions are mirrored in y-axis
                add_tiles(
                    creep_radius,
                    (
                        building_position[0],
                        building_position[1] - row_increment,
                    ),
                )

                # ----- decreasing size rows -----
                add_tiles(
                    creep_radius - row_increment,
                    (
                        building_position[0],
                        building_position[1] + row_increment + creep_radius / 2,
                    ),
                )

                # tile actions are mirrored in y-axis
                add_tiles(
                    creep_radius - row_increment,
                    (
                        building_position[0],
                        building_position[1] - row_increment - creep_radius / 2,
                    ),
                )

        map_tiles = game_map.width * game_map.height
        creep_coverage = round(len(self._creep_tiles) / map_tiles, 3)
        return (creep_coverage, len(self._creep_tiles)), creep_tumor_count, creep_tumors_died

    def calc_pac(self, summary_stats: Dict, game_length: int) -> Dict:
        game_length_minutes = game_length / 22.4 / 60

        if game_length_minutes > 0:
            pac_per_min = len(self.pac_list) / game_length_minutes
        else:
            pac_per_min = 0

        if self.pac_list:
            avg_pac_action_latency = sum(pac.actions[0] - pac.camera_moves[0][0] for pac in self.pac_list) / len(self.pac_list) / 22.4
            avg_actions_per_pac = sum(len(pac.actions) for pac in self.pac_list) / len(self.pac_list)
        else:
            avg_pac_action_latency = 0
            avg_actions_per_pac = 0

        pac_gaps = []
        for i in range(0, len(self.pac_list) - 1):
            pac_diff = self.pac_list[i + 1].initial_gameloop - self.pac_list[i].final_gameloop
            pac_gaps.append(pac_diff)
        if pac_gaps:
            avg_pac_gap = sum(pac_gaps) / len(pac_gaps) / 22.4
        else:
            avg_pac_gap = 0

        summary_stats['avg_pac_per_min'][self.player_id] = round(pac_per_min, 2)
        summary_stats['avg_pac_action_latency'][self.player_id] = round(avg_pac_action_latency, 2)
        summary_stats['avg_pac_actions'][self.player_id] = round(avg_actions_per_pac, 2)
        summary_stats['avg_pac_gap'][self.player_id] = round(avg_pac_gap, 2)
        return summary_stats

    def calc_sq(self, *, unspent_resources: int, collection_rate: int) -> float:
        sq = math.ceil(35 * (0.00137 * collection_rate - math.log(unspent_resources if unspent_resources > 0 else 1)) + 240)
        return sq
