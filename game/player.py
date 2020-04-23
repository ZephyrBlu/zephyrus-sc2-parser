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
        self.active_ability = None
        self.pac_list = []
        self.current_pac = None
        self.supply = 0
        self.supply_cap = 0
        self.supply_block = 0
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

    def calc_supply(self):
        total_supply = 0
        total_supply_provided = 0

        for obj_id, obj in self.objects.items():
            if obj.status == 'live' or ('Overlord' not in obj.name and obj.status == 'in_progress' and 'unit' in obj.type):
                total_supply += obj.supply
                total_supply_provided += obj.supply_provided

        self.supply = total_supply
        self.supply_cap = total_supply_provided

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
