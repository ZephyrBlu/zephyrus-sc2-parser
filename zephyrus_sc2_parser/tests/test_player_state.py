import pytest
from zephyrus_sc2_parser.game.game_obj import GameObj


player_resource_validation_testdata = [
    (
        {
            'minerals': [],
            'gas': [],
        },
        {
            'minerals': [],
            'gas': [],
        },
        {
            'minerals': 0,
            'gas': 0,
        },
        {
            'minerals': 0,
            'gas': 0,
        },
        0,
    ),
    (
        {
            'minerals': [1500],
            'gas': [500],
        },
        {
            'minerals': [500],
            'gas': [500],
        },
        {
            'minerals': 1500,
            'gas': 500,
        },
        {
            'minerals': 500,
            'gas': 500,
        },
        2000,
    ),
    (
        {
            'minerals': [1500, 1800],
            'gas': [500, 300],
        },
        {
            'minerals': [500, 700],
            'gas': [500, 200],
        },
        {
            'minerals': 1800,
            'gas': 300,
        },
        {
            'minerals': 700,
            'gas': 200,
        },
        2100,
    ),
]


@pytest.mark.parametrize(
    "player_collection_rates, player_unspent_resources, expected_collection_rate, expected_unspent_resources, expected_total_collection_rate",
    player_resource_validation_testdata
)
def test_create_object_summary_collection_rate_validation(
    player_collection_rates,
    player_unspent_resources,
    expected_collection_rate,
    expected_unspent_resources,
    expected_total_collection_rate,
):
    if not player_collection_rates['minerals']:
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
            'minerals': player_collection_rates['minerals'][-1],
            'gas': player_collection_rates['gas'][-1],
        }

        total_collection_rate = player_collection_rates['minerals'][-1] + player_collection_rates['gas'][-1]

        unspent_resources = {
            'minerals': player_unspent_resources['minerals'][-1],
            'gas': player_unspent_resources['gas'][-1],
        }

    assert collection_rate == expected_collection_rate
    assert unspent_resources == expected_unspent_resources
    assert total_collection_rate == expected_total_collection_rate


worker = GameObj('Probe', 1, 1, 1, 1, 50, 0)
worker_died = GameObj('Probe', 1, 1, 1, 1, 50, 0)
unit = GameObj('Stalker', 2, 2, 2, 2, 125, 50)
unit_died = GameObj('Stalker', 2, 2, 2, 2, 125, 50)

worker.type.extend(['unit', 'worker'])
worker_died.type.extend(['unit', 'worker'])
worker.status = 'live'
worker_died.status = 'died'
unit.type.append('unit')
unit_died.type.append('unit')
unit.status = 'live'
unit_died.status = 'died'

# need non-worker, worker and supply types
gather_game_objects_testdata = [
    (
        {},
        [],
        [],
        {
            'unit': {},
            'building': {},
            'upgrade': [],
            'current_selection': {},
            'workers_active': 0,
            'workers_killed': 0,
            'army_value': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_lost': {
                'minerals': 0,
                'gas': 0,
            },
            'total_army_value': 0,
            'total_resources_lost': 0,
        },
    ),
    (
        {},
        ['ZergMeleeWeaponsLevel1'],
        [],
        {
            'unit': {},
            'building': {},
            'upgrade': ['ZergMeleeWeaponsLevel1'],
            'current_selection': {},
            'workers_active': 0,
            'workers_killed': 0,
            'army_value': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_lost': {
                'minerals': 0,
                'gas': 0,
            },
            'total_army_value': 0,
            'total_resources_lost': 0,
        },
    ),
    (
        {1: worker},
        [],
        [],
        {
            'unit': {
                'Probe': {
                    'type': ['unit', 'worker'],
                    'live': 1,
                    'died': 0,
                    'in_progress': 0,
                    'mineral_cost': 50,
                    'gas_cost': 0,
                },
            },
            'building': {},
            'upgrade': [],
            'current_selection': {},
            'workers_active': 1,
            'workers_killed': 0,
            'army_value': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_lost': {
                'minerals': 0,
                'gas': 0,
            },
            'total_army_value': 0,
            'total_resources_lost': 0,
        }
    ),
    (
        {1: unit},
        [],
        [],
        {
            'unit': {
                'Stalker': {
                    'type': ['unit'],
                    'live': 1,
                    'died': 0,
                    'in_progress': 0,
                    'mineral_cost': 125,
                    'gas_cost': 50,
                },
            },
            'building': {},
            'upgrade': [],
            'current_selection': {},
            'workers_active': 0,
            'workers_killed': 0,
            'army_value': {
                'minerals': 125,
                'gas': 50,
            },
            'resources_lost': {
                'minerals': 0,
                'gas': 0,
            },
            'total_army_value': 175,
            'total_resources_lost': 0,
        }
    ),
    (
        {1: worker_died},
        [],
        [],
        {
            'unit': {
                'Probe': {
                    'type': ['unit', 'worker'],
                    'live': 0,
                    'died': 1,
                    'in_progress': 0,
                    'mineral_cost': 50,
                    'gas_cost': 0,
                },
            },
            'building': {},
            'upgrade': [],
            'current_selection': {},
            'workers_active': 0,
            'workers_killed': 1,
            'army_value': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_lost': {
                'minerals': 0,
                'gas': 0,
            },
            'total_army_value': 0,
            'total_resources_lost': 0,
        }
    ),
    (
        {1: unit_died},
        [],
        [],
        {
            'unit': {
                'Stalker': {
                    'type': ['unit'],
                    'live': 0,
                    'died': 1,
                    'in_progress': 0,
                    'mineral_cost': 125,
                    'gas_cost': 50,
                },
            },
            'building': {},
            'upgrade': [],
            'current_selection': {},
            'workers_active': 0,
            'workers_killed': 0,
            'army_value': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_lost': {
                'minerals': 125,
                'gas': 50,
            },
            'total_army_value': 0,
            'total_resources_lost': 175,
        }
    ),
    (
        {1: worker},
        [],
        [worker],
        {
            'unit': {
                'Probe': {
                    'type': ['unit', 'worker'],
                    'live': 1,
                    'died': 0,
                    'in_progress': 0,
                    'mineral_cost': 50,
                    'gas_cost': 0,
                },
            },
            'building': {},
            'upgrade': [],
            'current_selection': {'Probe': 1},
            'workers_active': 1,
            'workers_killed': 0,
            'army_value': {
                'minerals': 0,
                'gas': 0,
            },
            'resources_lost': {
                'minerals': 0,
                'gas': 0,
            },
            'total_army_value': 0,
            'total_resources_lost': 0,
        }
    ),
]


@pytest.mark.parametrize(
    "objects, player_upgrades, player_current_selection, expected_object_summary",
    gather_game_objects_testdata
)
def test_create_object_summary_gather_game_objects(
    objects,
    player_upgrades,
    player_current_selection,
    expected_object_summary,
):
    object_summary = {
        'unit': {},
        'building': {},
        'upgrade': [],
        'current_selection': {},
        'workers_active': 0,
        'workers_killed': 0,
        'army_value': {
            'minerals': 0,
            'gas': 0,
        },
        'resources_lost': {
            'minerals': 0,
            'gas': 0,
        },
        'total_army_value': 0,
        'total_resources_lost': 0,
    }

    for upg in player_upgrades:
        object_summary['upgrade'].append(upg)

    for obj in objects.values():
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

    for obj in player_current_selection:
        if obj.name not in object_summary['current_selection']:
            object_summary['current_selection'][obj.name] = 0
        object_summary['current_selection'][obj.name] += 1

    assert object_summary == expected_object_summary
