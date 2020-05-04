class GameObj:
    def __init__(self, name, obj_id, game_id, tag, priority, mineral_cost, gas_cost):
        self.name = name
        self.type = []
        self.obj_id = obj_id
        self.game_id = game_id
        self.tag = tag
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
        self.birth_time = None
        self.death_time = None
        self.morph_time = None
        self.position = None
        self.target = None
        self.status = None
        self.killed_by = None

    def __eq__(self, other):
        return self.game_id == other.game_id

    def __repr__(self):
        return f'({self.name}, {self.tag})'

    def calc_energy(self, gameloop):
        if not self.energy:
            return None

        # regen per gameloop
        energy_regen_rate = 0.03515625
        max_energy = 200

        def energy_maxout(current_gameloop, current_energy):
            return current_gameloop + ((max_energy - current_energy) / energy_regen_rate)

        current_gameloop = 0
        current_energy = self.energy
        for ability in self.abilities_used:
            if 'energy_cost' not in ability:
                continue

            if ability['used_at'] >=  energy_maxout(current_gameloop, current_energy):
                current_energy = 200
            else:
                current_energy += energy_regen_rate * (ability['used_at'] - current_gameloop)
            current_gameloop = ability['used_at']
            current_energy -= ability['energy_cost']

        if gameloop >=  energy_maxout(current_gameloop, current_energy):
            current_energy = 200
        else:
            current_energy += energy_regen_rate * (gameloop - current_gameloop)

        return current_energy

    def calc_inject_efficiency(self, gameloop):
        if not self.abilities_used:
            return None

        # only 1 inject = 100% efficiency
        if len(self.abilities_used) == 1:
            return 1

        # ~29sec
        inject_delay = 650

        missed_inject_time = 0
        current_gameloop = self.abilities_used[0][1]
        for i in range(1, len(self.abilities_used)):
            current_inject = self.abilities_used[i]

            time_diff = current_inject[1] - current_gameloop - 650

            # time diff < 0, inject was queued, 100% efficiency
            if time_diff > 0:
                missed_inject_time += time_diff
                current_gameloop = current_inject[1]
            else:
                current_gameloop = current_inject[1] + 650

        return 1 - (missed_inject_time / (current_gameloop - self.abilities_used[0][1] + 650))

    def calc_orbital_efficiency(self, gameloop):
        if not self.abilities_used:
            return None

        # only 1 inject = 100% efficiency
        if len(self.abilities_used) == 1:
            return 1

        orbital_efficiency = None
        ability_usage = {}
        for ability in self.abilities_used:
            print(ability)
            if ability[0]['ability_name'] not in ability_usage:
                ability_usage[ability[0]['ability_name']] = 0
            ability_usage[ability[0]['ability_name']] += 1

            current_energy = self.calc_energy(ability[1])
            print(current_energy)

        return 1 - (missed_inject_time / (current_gameloop - self.abilities_used[0][1] + 650))

