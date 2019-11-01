import pytest
from zephyrus_sc2_parser.game.game_obj import GameObj


mock_game_obj1 = GameObj(None, 1, 1, 1, None, None, None)
mock_game_obj2 = GameObj(None, 2, 2, 2, None, None, None)
mock_game_obj3 = GameObj(None, 3, 3, 3, None, None, None)

add_to_selection_testdata = [
    (
        None,
        [],
        {1: []},
        [],
        {},
        [],
    ),
    (
        1,
        [],
        {1: []},
        [],
        {},
        [],
    ),
    (
        None,
        [1],
        {1: []},
        [],
        {1: mock_game_obj1},
        [mock_game_obj1],
    ),
    (
        1,
        [1],
        {1: []},
        [],
        {1: mock_game_obj1},
        [mock_game_obj1],
    ),
    (
        None,
        [1],
        {1: []},
        [],
        {},
        [],
    ),
    (
        1,
        [1],
        {1: []},
        [],
        {},
        [],
    ),
    (
        None,
        [1],
        {1: [mock_game_obj2]},
        [],
        {1: mock_game_obj1, 2: mock_game_obj2},
        [mock_game_obj1],
    ),
    (
        1,
        [1],
        {1: [mock_game_obj2]},
        [],
        {1: mock_game_obj1, 2: mock_game_obj2},
        [mock_game_obj1, mock_game_obj2],
    ),
]


@pytest.mark.parametrize(
    "ctrl_group_num, new_obj_ids, player_control_groups, player_current_selection, player_objects, expected_selection",
    add_to_selection_testdata
)
def test_add_to_selection(
    ctrl_group_num,
    new_obj_ids,
    player_control_groups,
    player_current_selection,
    player_objects,
    expected_selection,
):
    if ctrl_group_num:
        selection = player_control_groups[ctrl_group_num]
    else:
        selection = player_current_selection

    for obj_game_id in new_obj_ids:
        if obj_game_id not in player_objects:
            return

    for obj_game_id in new_obj_ids:
        obj = player_objects[obj_game_id]
        selection.append(obj)

    selection.sort(key=lambda x: x.tag)

    assert selection == expected_selection


zero_indices_testdata = [
    # default state
    (
        {
            'm_delta': {
                'm_addUnitTags': [],
            }
        },
        None,
        'new',
        {},
        [],
        {},
        [],
    ),

    # adding single object to selection
    (
        {
            'm_delta': {
                'm_addUnitTags': [1],
            }
        },
        1,
        'new',
        {},
        [],
        {1: mock_game_obj1},
        [mock_game_obj1],
    ),

    # add multiple objects out of order to selection
    (
        {
            'm_delta': {
                'm_addUnitTags': [2, 1],
            }
        },
        1,
        'new',
        {},
        [],
        {1: mock_game_obj1, 2: mock_game_obj2},
        [mock_game_obj1, mock_game_obj2],
    ),

    # overwrite existing control group selection
    # with new object
    (
        {
            'm_delta': {
                'm_addUnitTags': [1],
            }
        },
        1,
        'new',
        {1: [mock_game_obj2]},
        [],
        {1: mock_game_obj1, 2: mock_game_obj2},
        [mock_game_obj1],
    ),

    # overwrite existing player selection
    # with new object
    (
        {
            'm_delta': {
                'm_addUnitTags': [1],
            }
        },
        None,
        'new',
        {},
        [mock_game_obj2],
        {1: mock_game_obj1, 2: mock_game_obj2},
        [mock_game_obj1],
    ),

    # no ctrl group deletion w single object
    (
        {
            'm_delta': {
                'm_addUnitTags': [],
                'm_removeMask': {'ZeroIndices': [0]},
            }
        },
        None,
        'sub',
        {},
        [mock_game_obj1],
        {},
        [mock_game_obj1],
    ),

    # no ctrl group deletion w multiple objects
    (
        {
            'm_delta': {
                'm_addUnitTags': [],
                'm_removeMask': {'ZeroIndices': [0]},
            }
        },
        None,
        'sub',
        {},
        [mock_game_obj1, mock_game_obj2],
        {},
        [mock_game_obj1],
    ),

    # ctrl group deletion w single object
    (
        {
            'm_delta': {
                'm_addUnitTags': [],
                'm_removeMask': {'ZeroIndices': [0]},
            }
        },
        1,
        'sub',
        {1: [mock_game_obj1]},
        [],
        {},
        [mock_game_obj1],
    ),

    # ctrl group deletion w multiple objects
    (
        {
            'm_delta': {
                'm_addUnitTags': [],
                'm_removeMask': {'ZeroIndices': [0]},
            }
        },
        1,
        'sub',
        {1: [mock_game_obj1, mock_game_obj2]},
        [],
        {},
        [mock_game_obj1],
    ),
]


@pytest.mark.parametrize(
    "event, ctrl_group_num, selection_type, player_control_groups, player_current_selection, player_objects, expected_selection",
    zero_indices_testdata,
)
def test_handle_zero_indices(
    event,
    ctrl_group_num,
    selection_type,
    player_control_groups,
    player_current_selection,
    player_objects,
    expected_selection,
):

    if selection_type == 'new':
        if ctrl_group_num:
            player_control_groups[ctrl_group_num] = []
            selection = player_control_groups[ctrl_group_num]
        else:
            player_current_selection = []
            selection = player_current_selection

        new_game_ids = event['m_delta']['m_addUnitTags']

        for obj_game_id in new_game_ids:
            if obj_game_id in player_objects:
                selection.append(player_objects[obj_game_id])
        selection.sort(key=lambda x: x.tag)

    elif selection_type == 'sub':
        if ctrl_group_num:
            selection = player_control_groups[ctrl_group_num]
        else:
            selection = player_current_selection

        selection_indices = event['m_delta']['m_removeMask']['ZeroIndices']

        for i in range(len(selection) - 1, -1, -1):
            if i not in selection_indices:
                del selection[i]

    assert selection == expected_selection


one_indices_testdata = [
    (
        {
            'm_delta': {'m_removeMask': {'OneIndices': []}},
        },
        None,
        'new',
        {},
        [],
        [],
    ),
    (
        {
            'm_delta': {'m_removeMask': {'OneIndices': []}},
        },
        1,
        'new',
        {1: []},
        [],
        [],
    ),
    (
        {
            'm_delta': {'m_removeMask': {'OneIndices': [0]}},
        },
        None,
        'new',
        {},
        [mock_game_obj1],
        [],
    ),
    (
        {
            'm_delta': {'m_removeMask': {'OneIndices': [0]}},
        },
        1,
        'new',
        {1: [mock_game_obj1]},
        [],
        [],
    ),
]


@pytest.mark.parametrize(
    "event, ctrl_group_num, selection_type, player_control_groups, player_current_selection, expected_selection",
    one_indices_testdata,
)
def test_handle_one_indices(
    event,
    ctrl_group_num,
    selection_type,
    player_control_groups,
    player_current_selection,
    expected_selection,
):
    selection_indices = event['m_delta']['m_removeMask']['OneIndices']

    if ctrl_group_num:
        selection = player_control_groups[ctrl_group_num]
    else:
        selection = player_current_selection

    for i in range(len(selection) - 1, -1, -1):
        if i in selection_indices:
            del selection[i]

    assert selection == expected_selection
