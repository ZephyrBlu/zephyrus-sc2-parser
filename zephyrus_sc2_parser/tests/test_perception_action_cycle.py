import pytest


check_position_testdata = [
    # initial_camera_position test cases
    ((0, 0), (0, 0), True),
    ((0, 0), (5, 0), True),
    ((0, 0), (0, 5), True),
    ((0, 0), (6, 0), True),
    ((0, 0), (0, 6), True),
    ((0, 0), (7, 0), False),
    ((0, 0), (0, 7), False),
    ((0, 0), (3, 2), True),
    ((0, 0), (3, 3), True),
    ((0, 0), (3, 4), False),

    # new_position test cases
    ((5, 0), (0, 0), True),
    ((0, 5), (0, 0), True),
    ((6, 0), (0, 0), True),
    ((0, 6), (0, 0), True),
    ((7, 0), (0, 0), False),
    ((0, 7), (0, 0), False),
    ((3, 2), (0, 0), True),
    ((3, 3), (0, 0), True),
    ((3, 4), (0, 0), False),
]


@pytest.mark.parametrize("new_position, initial_camera_position, expected", check_position_testdata)
def test_check_position(new_position, initial_camera_position, expected):
    x_diff = abs(new_position[0] - initial_camera_position[0])
    y_diff = abs(new_position[1] - initial_camera_position[1])
    total_diff = x_diff + y_diff

    if total_diff > 6:
        assert expected is False
    else:
        assert expected is True


check_duration_testdata = [
    (0, 0, False),
    (0, 3, False),
    (0, 4, False),
    (0, 5, True),
]


@pytest.mark.parametrize("initial_gameloop, new_gameloop, expected", check_duration_testdata)
def test_check_duration(initial_gameloop, new_gameloop, expected):
    if new_gameloop - initial_gameloop > 4:
        assert expected is True
    else:
        assert expected is False
