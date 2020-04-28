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
        self.supply = 0
        self.supply_provided = 0
        self.cooldown = None
        self.queue = None
        self.control_groups = {}
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
