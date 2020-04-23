class PlayerState:
    def __init__(self, player, gameloop):
        self.player = player
        self.gameloop = gameloop
        self.summary = self.create_object_summary()

    def create_object_summary(self):
        if not self.player.collection_rate['minerals']:
            collection_rate = {
                'minerals': 0,
                'gas': 0,
            }

            total_collection_rate = 0

            unspent_resources = {
                'minerals': 0,
                'gas': 0,
            }
        else:
            collection_rate = {
                'minerals': self.player.collection_rate['minerals'][-1],
                'gas': self.player.collection_rate['gas'][-1],
            }

            total_collection_rate = self.player.collection_rate['minerals'][-1] + self.player.collection_rate['gas'][-1]

            unspent_resources = {
                'minerals': self.player.unspent_resources['minerals'][-1],
                'gas': self.player.unspent_resources['gas'][-1],
            }

        object_summary = {
            'gameloop': self.gameloop,
            'resource_collection_rate': collection_rate,
            'unspent_resources': unspent_resources,
            'resource_collection_rate_all': total_collection_rate,
            'unit': {},
            'building': {},
            'upgrade': [],
            'current_selection': {},
            'workers_active': 0,
            'workers_killed': 0,
            'supply': self.player.supply,
            'supply_cap': self.player.supply_cap,
            'supply_block': self.player.supply_block,
            'army_value': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_lost': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_collected': {
                'minerals': self.player.resources_collected['minerals'],
                'gas': self.player.resources_collected['gas'],
            },
            'total_army_value': 0,
            'total_resources_lost': 0,
            'total_resouces_collected': 0,
        }

        for upg in self.player.upgrades:
            object_summary['upgrade'].append(upg)

        for obj in self.player.objects.values():
            worker = False
            for obj_type in obj.type:
                if obj_type == 'worker':
                    worker = True
                elif obj_type != 'supply':
                    if obj.name not in object_summary[obj_type]:
                        object_summary[obj_type][obj.name] = {
                            'type': [obj_type],
                            'live': 0,
                            'died': 0,
                            'in_progress': 0,
                            'supply': obj.supply,
                            'supply_provided': obj.supply_provided,
                            'mineral_cost': obj.mineral_cost,
                            'gas_cost': obj.gas_cost,
                        }

                    object_summary[obj_type][obj.name][obj.status] += 1
            if worker:
                if obj.status == 'live':
                    object_summary['workers_active'] += 1
                elif obj.status == 'died':
                    object_summary['workers_killed'] += 1

                if 'worker' not in object_summary['unit'][obj.name]['type']:
                    object_summary['unit'][obj.name]['type'].append('worker')

            elif 'unit' in obj.type:
                if obj.status == 'live':
                    object_summary['army_value']['minerals'] += obj.mineral_cost
                    object_summary['army_value']['gas'] += obj.gas_cost
                    object_summary['total_army_value'] += obj.mineral_cost + obj.gas_cost
                elif obj.status == 'died':
                    object_summary['resources_lost']['minerals'] += obj.mineral_cost
                    object_summary['resources_lost']['gas'] += obj.gas_cost
                    object_summary['total_resources_lost'] += obj.mineral_cost + obj.gas_cost

        for obj in self.player.current_selection:
            if obj.name not in object_summary['current_selection']:
                object_summary['current_selection'][obj.name] = 0
            object_summary['current_selection'][obj.name] += 1

        return object_summary
