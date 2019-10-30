import pytest


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
    ),
]


@pytest.mark.parametrize(
    "player_collection_rates, player_unspent_resources, expected_collection_rate, expected_unspent_resources",
    player_resource_validation_testdata
)
def test_create_object_summary_collection_rate_validation(
    player_collection_rates,
    player_unspent_resources,
    expected_collection_rate,
    expected_unspent_resources
):
    if not player_collection_rates['minerals']:
        collection_rate = {
            'minerals': 0,
            'gas': 0,
        }

        unspent_resources = {
            'minerals': 0,
            'gas': 0,
        }
    else:
        collection_rate = {
            'minerals': player_collection_rates['minerals'][-1],
            'gas': player_collection_rates['gas'][-1],
        }

        unspent_resources = {
            'minerals': player_unspent_resources['minerals'][-1],
            'gas': player_unspent_resources['gas'][-1],
        }

    assert collection_rate == expected_collection_rate
    assert unspent_resources == expected_unspent_resources


# need non-worker, worker and supply types
gather_game_objects_testdata = [
    ({}, {}),
]


@pytest.mark.parametrize("objects, expected_object_summary", gather_game_objects_testdata)
def test_create_object_summary_gather_game_objects(objects, expected_object_summary):
    object_summary = {
        'gameloop': None,
        'resource_collection_rate': None,
        'unspent_resources': None,
        'unit': {},
        'building': {},
        'current_selection': None,
    }

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
        if worker and 'worker' not in object_summary['unit'][obj.name]['type']:
            object_summary['unit'][obj.name]['type'].append('worker')


add_to_current_selection_testdata = [
    ({}, {}),
]


@pytest.mark.parametrize(
    "player_current_selection, expected_current_selection",
    add_to_current_selection_testdata
)
def test_create_object_summary_add_to_current_selection(
    player_current_selection, expected_current_selection
):
    object_summary = {
        'gameloop': None,
        'resource_collection_rate': None,
        'unspent_resources': None,
        'unit': None,
        'building': None,
        'current_selection': {},
    }

    for obj in player_current_selection:
        if obj.name not in object_summary['current_selection']:
            object_summary['current_selection'][obj.name] = 0
        object_summary['current_selection'][obj.name] += 1
