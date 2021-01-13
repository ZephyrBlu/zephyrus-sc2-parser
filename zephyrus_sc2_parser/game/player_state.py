from typing import Dict, Any
from zephyrus_sc2_parser.dataclasses import Gameloop
from zephyrus_sc2_parser.game import Game, GameObj, Player


class PlayerState:
    """
    Contains a summary of a player's gamestate at a particular gameloop,
    plus references to the game and player
    """
    def __init__(self, game: Game, player: Player, gameloop: Gameloop):
        self.game: Game = game
        self.player: Player = player
        self.gameloop: Gameloop = gameloop
        self.summary: Dict[str, Any] = self._create_object_summary()

    def _create_object_summary(self) -> Dict[str, Any]:
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
            'workers_produced': 0,
            'workers_lost': 0,
            'supply': self.player.supply,
            'supply_cap': self.player.supply_cap,
            'supply_block': round(self.player.supply_block / 22.4, 1),
            'spm': 0,
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
            'total_resources_collected': self.player.resources_collected['minerals'] + self.player.resources_collected['gas'],
            'race': {},
        }

        object_summary['spm'] = self.player.calc_spm(self.gameloop, recent=True)

        # if warpgate_efficiency isn't default
        if self.player.warpgate_efficiency[0] > 0:
            object_summary['race']['warpgate_efficiency'] = (
                round(1 - self.player.warpgate_efficiency[1] / self.player.warpgate_efficiency[0], 3),
                round(self.player.warpgate_efficiency[1] / 22.4, 1),
            )

        for upg in self.player.upgrades:
            object_summary['upgrade'].append(upg.name)

        if self.player.race == 'Zerg':
            map_creep_coverage, tumors_active, tumors_died = self.player.calc_creep(self.game.map)

            # if the creep flag is disabled calc_creep will return None, None
            # need to check for int as 0 is falsy
            if map_creep_coverage and type(tumors_active) == int and type(tumors_died) == int:
                object_summary['race']['creep'] = {
                    'coverage': map_creep_coverage,
                    'tumors_active': tumors_active,
                    'tumors_died': tumors_active,
                }

        current_idle_larva = 0
        for obj in self.player.objects.values():
            # High Templars and Drones die when they morph, should not be counted
            if (obj.name == 'HighTemplar' or obj.name == 'Drone') and obj.morph_time:
                continue

            if obj.name == 'Larva' and obj.status == GameObj.LIVE:
                current_idle_larva += 1

            worker = False
            for current_type in obj.type:
                if current_type == GameObj.WORKER:
                    worker = True
                elif current_type != GameObj.SUPPLY:
                    if obj.name not in object_summary[current_type.lower()]:
                        object_summary[current_type.lower()][obj.name] = {
                            'type': [current_type],
                            'live': 0,
                            'died': 0,
                            'in_progress': 0,
                            'supply': obj.supply,
                            'supply_provided': obj.supply_provided,
                            'mineral_cost': obj.mineral_cost,
                            'gas_cost': obj.gas_cost,
                        }
                    # convert to lowercase for serialization
                    object_summary[current_type.lower()][obj.name][obj.status.lower()] += 1

                    command_structures = ['Hatchery', 'Lair', 'Hive', 'Nexus', 'OrbitalCommand']

                    # Nexus, Orbital and Hatchery calculations
                    if current_type == GameObj.BUILDING and (obj.name in command_structures):
                        obj_energy = obj.calc_energy(self.gameloop)
                        if obj_energy and obj.status == 'live':
                            if 'energy' not in object_summary['race']:
                                object_summary['race']['energy'] = {}

                            if 'abilities_used' not in object_summary['race']:
                                object_summary['race']['abilities_used'] = {}

                            if self.player.race == 'Protoss' and 'ability_targets' not in object_summary['race']:
                                object_summary['race']['ability_targets'] = {}

                            if obj.name not in object_summary['race']['energy']:
                                object_summary['race']['energy'][obj.name] = []
                            object_summary['race']['energy'][obj.name].append((obj_energy, *obj.energy_efficiency))

                            for ability, ability_target, ability_gameloop in obj.abilities_used:
                                if ability.name not in object_summary['race']['abilities_used']:
                                    object_summary['race']['abilities_used'][ability.name] = 0
                                object_summary['race']['abilities_used'][ability.name] += 1

                                if 'ability_targets' in object_summary['race'] and ability_target:
                                    if ability_target.name not in object_summary['race']['ability_targets']:
                                        object_summary['race']['ability_targets'][ability_target.name] = 0
                                    object_summary['race']['ability_targets'][ability_target.name] += 1

                        obj_inject_efficiency = obj.calc_inject_efficiency(self.gameloop)
                        if obj_inject_efficiency:
                            if 'inject_efficiency' not in object_summary['race']:
                                object_summary['race']['inject_efficiency'] = []
                            object_summary['race']['inject_efficiency'].append(obj_inject_efficiency)

            if current_idle_larva:
                self.player.idle_larva.append(current_idle_larva)

            if worker:
                if obj.status == GameObj.LIVE:
                    object_summary['workers_active'] += 1
                elif obj.status == GameObj.DIED:
                    object_summary['workers_lost'] += 1
                object_summary['workers_produced'] += 1

                if GameObj.WORKER not in object_summary['unit'][obj.name]['type']:
                    object_summary['unit'][obj.name]['type'].append(GameObj.WORKER)

            elif GameObj.UNIT in obj.type:
                if obj.status == GameObj.LIVE:
                    object_summary['army_value']['minerals'] += obj.mineral_cost
                    object_summary['army_value']['gas'] += obj.gas_cost
                    object_summary['total_army_value'] += obj.mineral_cost + obj.gas_cost
                elif obj.status == GameObj.DIED:
                    object_summary['resources_lost']['minerals'] += obj.mineral_cost
                    object_summary['resources_lost']['gas'] += obj.gas_cost
                    object_summary['total_resources_lost'] += obj.mineral_cost + obj.gas_cost

        for obj in self.player.current_selection:
            if obj.name not in object_summary['current_selection']:
                object_summary['current_selection'][obj.name] = 0
            object_summary['current_selection'][obj.name] += 1

        return object_summary
