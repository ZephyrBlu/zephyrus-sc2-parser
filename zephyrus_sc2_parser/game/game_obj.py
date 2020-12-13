import math


class GameObj:
    # obj statuses
    LIVE = 'LIVE'
    DIED = 'DIED'
    IN_PROGRESS = 'IN_PROGRESS'

    # obj types
    UNIT = 'UNIT'
    BUILDING = 'BUILDING'
    WORKER = 'WORKER'
    SUPPLY = 'SUPPLY'

    def __init__(self, name, obj_id, game_id, tag, recycle, priority, mineral_cost, gas_cost):
        self.name = name
        self.type = []
        self.obj_id = obj_id
        self.game_id = game_id
        self.tag = tag
        self.recycle = recycle
        self.priority = priority
        self.mineral_cost = mineral_cost
        self.gas_cost = gas_cost
        self.energy = None
        self.supply = 0
        self.supply_provided = 0
        self.cooldown = None
        self.queue = None
        self.control_groups = {}
        self.abilities_used = []
        self.energy_efficiency = None
        self.init_time = None
        self.birth_time = None
        self.death_time = None
        self.morph_time = None
        self.position = None
        self.target = None
        self.status = None
        self.killed_by = None

    def __eq__(self, other):
        return self.game_id == other.game_id

    def __hash__(self):
        return hash(self.game_id)

    def __repr__(self):
        return f'({self.name}, {self.tag})'

    def calc_distance(self, other_position):
        # position contains x, y, z in integer form of floats
        # simple pythagoras theorem calculation
        x_diff = abs(self.position.x - other_position.x)
        y_diff = abs(self.position.y - other_position.y)
        distance = math.sqrt(x_diff ** 2 + y_diff ** 2)
        return distance

    def calc_energy(self, gameloop):
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
                    self.energy_efficiency = (1, round(time_past_min_energy / 22.4, 1))

        if gameloop >= energy_maxout(current_gameloop, current_energy, max_energy):
            current_energy = max_energy
        else:
            current_energy += energy_regen_rate * (gameloop - current_gameloop)

        return round(current_energy, 1)

    def calc_inject_efficiency(self, gameloop):
        if not self.abilities_used or self.name not in ['Hatchery', 'Lair', 'Hive']:
            return None

        # only 1 inject = 100% efficiency
        if len(self.abilities_used) == 1:
            return 1

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
