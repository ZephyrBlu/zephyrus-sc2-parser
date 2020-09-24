from zephyrus_sc2_parser.events.base_event import BaseEvent


class UnitPositionsEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def _find_unit(self, unit_index):
        for p in self.game.players.values():
            for u in p.objects.values():
                # return unit if it hasn't died, or died in the last 240 gameloops (~10sec)
                if (
                    u.tag == unit_index
                    and u.name != 'Larva'
                    and u.name != 'Egg'
                    and u.name != 'Queen'
                    and 'worker' not in u.type
                    and 'supply' not in u.type
                    and (u.status != 'died' or (self.gameloop - u.death_time) <= 240)
                ):
                    return u, p
        return None, None

    def parse_event(self):
        game = self.game
        event = self.event
        gameloop = self.gameloop
        inital_units = {
            1: [],
            2: [],
        }

        engagement = {
            1: [],
            2: [],
        }

        army_position = {
            1: None,
            2: None,
        }

        position_proportion = {
            1: None,
            2: None,
        }

        distance_to_command_structure = {
            1: {
                1: None,
                2: None,
            },
            2: {
                1: None,
                2: None,
            },
        }

        command_structures = [
            'Nexus',
            'CommandCenter',
            'OrbitalCommand',
            'PlanetaryFortress',
            'Hatchery',
            'Lair',
            'Hive',
        ]

        engagement_resources = {
            1: {
                'live': 0,
                'died': 0,
            },
            2: {
                'live': 0,
                'died': 0,
            },
        }

        unit_index = event['m_firstUnitIndex']
        for i in range(0, len(event['m_items']), 3):
            unit_index += event['m_items'][i + 0]
            unit_x = event['m_items'][i + 1]
            unit_y = event['m_items'][i + 2]
            # unit identified by unitIndex at the current event['_gameloop'] time is at approximate position (x, y)

            current_unit, unit_owner = self._find_unit(unit_index)
            if current_unit and unit_owner:
                current_unit.position = {
                    'x': unit_x,
                    'y': unit_y,
                }
                current_unit.prev_positions.append((gameloop, current_unit.position))
                current_unit.target_position = None
                inital_units[unit_owner.player_id].append(current_unit)

        for p in game.players.values():
            for obj in p.objects.values():
                # filter out buildings and units that didn't die within the last 240 gameloops
                if (
                    'died' in obj.status
                    and obj.name != 'Larva'
                    and obj.name != 'Egg'
                    and obj.name != 'Queen'
                    and obj.death_time >= (gameloop - 240)
                    and 'building' not in obj.type
                    and 'supply' not in obj.type
                    and 'worker' not in obj.type
                ):
                    inital_units[p.player_id].append(obj)

        for player_id, units in inital_units.items():
            all_unit_distances = {}

            if len(units) == 1:
                army_position[player_id] = units[0].position
                continue

            print(game.players[player_id].name, round(gameloop / 22.4 / 60, 2))
            for unit in units:
                unit_distances = []
                for compare_unit in units:
                    if unit != compare_unit:
                        # calculate distance between units
                        current_distance = unit.calc_distance(compare_unit.position)
                        if current_distance <= 10:
                            # print((unit.name, unit.position), (compare_unit.name, compare_unit.position))
                            unit_distances.append((compare_unit, current_distance))
                if unit_distances:
                    all_unit_distances[unit] = unit_distances

            # calculate average distance to current unit position
            max_unit_count = (None, 0, 0)
            if all_unit_distances:
                for unit, unit_distances in all_unit_distances.items():
                    avg_unit_distance = sum(map(lambda x: x[1], unit_distances)) / len(unit_distances)
                    if (
                        len(unit_distances) > max_unit_count[1]
                        or (
                            len(unit_distances) == max_unit_count[1]
                            and avg_unit_distance < max_unit_count[2]
                        )
                    ):
                        max_unit_count = (unit, len(unit_distances), avg_unit_distance)
            print('\n')
            if max_unit_count[0]:
                army_position[player_id] = max_unit_count[0].position

                # add engagement info for army units inside 10 tile radius of army center
                for army_unit, unit_distance in all_unit_distances[max_unit_count[0]]:
                    engagement[player_id].append(army_unit)
                    if army_unit.status not in engagement_resources[player_id]:
                        engagement_resources[player_id][army_unit.status] = 0
                    print(army_unit.name, army_unit.status, army_unit.position)
                    engagement_resources[player_id][army_unit.status] += army_unit.mineral_cost
                    engagement_resources[player_id][army_unit.status] += army_unit.gas_cost
                # add engagement info for center army unit
                engagement_resources[player_id][max_unit_count[0].status] += max_unit_count[0].mineral_cost
                engagement_resources[player_id][max_unit_count[0].status] += max_unit_count[0].gas_cost
        print('\n')

        total_engagement_resources = {
            1: engagement_resources[1]['live'] + engagement_resources[1]['died'],
            2: engagement_resources[2]['live'] + engagement_resources[2]['died'],
        }
        for p_id, current_army_position in army_position.items():
            if not current_army_position: # or total_engagement_resources[p_id] < 2000:
                continue

            for player in game.players.values():
                min_structure_distance = None
                for obj in player.objects.values():
                    if obj.name in command_structures and obj.status != 'died':
                        structure_distance = obj.calc_distance(current_army_position)
                        if not min_structure_distance or structure_distance < min_structure_distance[0]:
                            min_structure_distance = (structure_distance, obj)
                if min_structure_distance:
                    distance_to_command_structure[p_id][player.player_id] = min_structure_distance[0]

        army_position_proportion = None
        for player_id, structure_distances in distance_to_command_structure.items():
            opp_id = 1 if player_id == 2 else 2
            player_distance = structure_distances[player_id]
            opp_distance = structure_distances[opp_id]

            if not player_distance or not opp_distance:
                continue

            total_distance = player_distance + opp_distance

            # to prevent proxy structures from interfering
            if total_distance < 50:
                continue

            # calculate proportion of distance to each base, limiting value to domain of -1 to 1
            # then add 1 to bring domain to 0 to 2, then half to bring domain to 0 to 1
            army_position_proportion = (((player_distance / total_distance) - (opp_distance / total_distance)) + 1) / 2
            print(game.players[player_id].name, army_position_proportion, f'Player: {player_distance}', f'Opponent: {opp_distance}')
            game.players[player_id].army_positions.append((army_position_proportion, player_distance, army_position[player_id], total_engagement_resources[player_id], gameloop))
            position_proportion[player_id] = army_position_proportion

        if army_position_proportion:
            p1_total_collection_rate = game.players[1].collection_rate['minerals'][-1] + game.players[1].collection_rate['gas'][-1]
            p2_total_collection_rate = game.players[2].collection_rate['minerals'][-1] + game.players[2].collection_rate['gas'][-1]

            game.engagements.append({
                'gameloop': gameloop,
                1: {
                    'units': engagement[1],
                    'total_collection_rate': p1_total_collection_rate,
                    'army_value': engagement_resources[1],
                    'army_position': army_position[1],
                    'relative_position': position_proportion[1],
                },
                2: {
                    'units': engagement[2],
                    'total_collection_rate': p2_total_collection_rate,
                    'army_value': engagement_resources[2],
                    'army_position': army_position[2],
                    'relative_position': position_proportion[2],
                },
            })
