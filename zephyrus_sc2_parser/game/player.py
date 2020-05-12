import math


class Player:
    def __init__(self, player_id, profile_id, region_id, realm_id, name, race):
        self.player_id = player_id

        if type(name) is bytes:
            self.name = name.decode('utf-8')
        else:
            self.name = name
        if type(name) is bytes:
            self.race = race.decode('utf-8')
        else:
            self.race = race

        self.user_id = None
        self.profile_id = profile_id
        self.region_id = region_id
        self.realm_id = realm_id
        self.objects = {}
        self.upgrades = []
        self.current_selection = []
        self.control_groups = {}
        self.warpgate_cooldowns = []
        self.warpgate_efficiency = (0, 0)
        self.active_ability = None
        self.pac_list = []
        self.current_pac = None
        self.prev_screen_position = None
        self.screens = []
        self.supply = 0
        self.supply_cap = 0
        self.supply_block = 0
        self.idle_larva = []
        self._creep_tiles = None
        self.unspent_resources = {
            'minerals': [],
            'gas': [],
        }
        self.collection_rate = {
            'minerals': [],
            'gas': [],
        }
        self.resources_collected = {
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

    def calc_spm(self, gameloop, *, recent=False):
        if not recent:
            return round(len(self.screens) / (gameloop / 22.4 / 60), 1)

        # 1 minute in gameloops
        gameloop_minute = 1344
        prev_minute_screens = 0

        for screen_gameloop in self.screens:
            if screen_gameloop >= gameloop - gameloop_minute:
                prev_minute_screens += 1

        return prev_minute_screens

    def calc_creep(self, map_info):
        if self.race != 'Zerg':
            return None, None

        if not self._creep_tiles:
            self._creep_tiles = set()

        creep_tumor_count = 0
        for obj in self.objects.values():
            if obj.status != 'live':
                continue

            # odd tile objects position += 0.5. Rounded off in events
            if obj.name == 'Hatchery' or obj.name == 'Lair' or obj.name == 'Hive':
                creep_radius = 12
            elif obj.name == 'CreepTumorBurrowed':
                creep_tumor_count += 1
                creep_radius = 10
            else:
                continue

            # add 0.5 to get center of central tile
            building_position = (obj.position['x'] + 0.5, obj.position['y'] + 0.5)

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

            for i in range(0, creep_radius//2):
                row_increment = i + 1

                # ----- full-size rows -----
                # add radius/2 full-size rows to improve area approximation
                add_tiles(
                    creep_radius,
                    (building_position[0], building_position[1] + row_increment),
                )

                # tile actions are mirrored in y-axis
                add_tiles(
                    creep_radius,
                    (building_position[0], building_position[1] - row_increment),
                )

                # ----- decreasing size rows -----
                add_tiles(
                    creep_radius - row_increment,
                    (
                        building_position[0],
                        building_position[1] + row_increment + creep_radius/2
                    ),
                )

                # tile actions are mirrored in y-axis
                add_tiles(
                    creep_radius - row_increment,
                    (
                        building_position[0],
                        building_position[1] - row_increment - creep_radius/2
                    ),
                )

        map_tiles = map_info['width'] * map_info['height']
        creep_coverage = round(len(self._creep_tiles) / map_tiles, 3)

        return (creep_coverage, len(self._creep_tiles)), creep_tumor_count

    def calc_pac(self, summary_stats, game_length):
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
        for i in range(0, len(self.pac_list)-1):
            pac_diff = self.pac_list[i+1].initial_gameloop - self.pac_list[i].final_gameloop
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

    def calc_sq(self, *, unspent_resources, collection_rate):
        sq = math.ceil(35 * (0.00137 * collection_rate - math.log(unspent_resources if unspent_resources > 0 else 1)) + 240)
        return sq
