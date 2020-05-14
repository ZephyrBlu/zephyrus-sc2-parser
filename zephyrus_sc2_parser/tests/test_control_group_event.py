import pytest
from zephyrus_sc2_parser.game.game_obj import GameObj


mock_obj = GameObj(None, None, 1, 1, None, None, None)
mock_obj2 = GameObj(None, None, 2, 2, None, None, None)
set_obj_group_info_testdata = [
    (1, {1: []}, None),
    (1, {1: [mock_obj]}, [(1, 0)]),
    (1, {1: [mock_obj, mock_obj2]}, [(1, 0), (1, 1)]),
]


@pytest.mark.parametrize(
    "ctrl_group_num, player_control_groups, expected_indexes",
    set_obj_group_info_testdata,
)
def test_set_obj_group_info(ctrl_group_num, player_control_groups, expected_indexes):
    ctrl_group = player_control_groups[ctrl_group_num]

    for index, obj in enumerate(ctrl_group):
        obj.control_groups[ctrl_group_num] = index

    for i in range(0, len(ctrl_group)):
        assert ctrl_group[i].control_groups[ctrl_group_num] == expected_indexes[i][1]


mock_obj.control_groups[1] = 0
mock_obj2.control_groups[1] = 1
mock_obj3 = GameObj(None, None, 3, 3, None, None, None)
mock_obj3.control_groups[1] = 2
mock_obj3.control_groups[2] = 0

mock_obj4 = GameObj(None, None, 4, 4, None, None, None)
mock_obj4.control_groups[1] = 0
mock_obj4.control_groups[2] = 0


remove_obj_group_info_testdata = [
    (1, {1: [mock_obj]}, [{}]),
    (1, {1: [mock_obj, mock_obj2]}, [{}, {}]),
    (1, {1: [mock_obj, mock_obj2, mock_obj3], 2: [mock_obj3]}, [{}, {}, {2: 0}]),
    (2, {1: [mock_obj4], 2: [mock_obj4]}, [{1: 0}]),
]


@pytest.mark.parametrize(
    "ctrl_group_num, player_control_groups, expected_indexes",
    remove_obj_group_info_testdata,
)
def test_remove_obj_group_info(ctrl_group_num, player_control_groups, expected_indexes):
    ctrl_group = player_control_groups[ctrl_group_num]

    for index, obj in enumerate(ctrl_group):
        for group_num, group_info in obj.control_groups.items():
            if ctrl_group_num == group_num and index == group_info:
                del obj.control_groups[group_num]
                break

    for index, obj in enumerate(ctrl_group):
        assert obj.control_groups == expected_indexes[index]


copy_from_selection_testdata = [
    ([], [], []),
    ([], [mock_obj, mock_obj2], [mock_obj, mock_obj2]),
    ([mock_obj], [mock_obj2, mock_obj3], [mock_obj, mock_obj2, mock_obj3]),
]


@pytest.mark.parametrize("target, selection, expected", copy_from_selection_testdata)
def test_copy_from_selection(target, selection, expected):
    for obj in selection:
        if obj not in target:
            target.append(obj)

    assert target == expected


add_to_group_testdata = [
    ([], {1: []}, 1, []),
    ([mock_obj], {1: []}, 1, [mock_obj]),
    ([mock_obj, mock_obj2], {1: []}, 1, [mock_obj, mock_obj2]),
    ([mock_obj], {1: [mock_obj]}, 1, [mock_obj]),
    ([mock_obj, mock_obj2], {1: [mock_obj]}, 1, [mock_obj, mock_obj2]),
    ([mock_obj, mock_obj2], {1: [mock_obj, mock_obj2]}, 1, [mock_obj, mock_obj2]),
]


@pytest.mark.parametrize(
    "player_current_selection, player_control_groups, ctrl_group_num, expected_group",
    add_to_group_testdata
)
def test_add_to_group(
    player_current_selection,
    player_control_groups,
    ctrl_group_num,
    expected_group,
):
    new_obj_list = player_current_selection
    control_group = player_control_groups[ctrl_group_num]

    for new_obj in new_obj_list:
        duplicate = False
        for old_obj in control_group:
            if new_obj.game_id == old_obj.game_id:
                duplicate = True
                break

        if not duplicate:
            control_group.append(new_obj)

    control_group.sort(key=lambda x: x.tag)

    assert control_group == expected_group


# integration test???
# remove_from_group_testdata = [
#     (),
# ]


# @pytest.mark.parametrize("", remove_from_group_testdata)
# def test_remove_from_group(player_control_groups, ctrl_group_num, event):
#     mask_x = event['m_mask']['Mask'][0]
#     mask_y = event['m_mask']['Mask'][1]
#     length = len(player_control_groups[ctrl_group_num])

#     bitmask = self._create_bitmask(mask_x, mask_y, length)

#     for i in range(length - 1, -1, -1):
#         if bitmask[i] == '1':
#             del player_control_groups[ctrl_group_num][i]

# parse_event is integration test
