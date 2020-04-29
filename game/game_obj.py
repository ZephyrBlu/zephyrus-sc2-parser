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
