import pytest
import math


create_bitmask_testdata = [
    # 2 units selected
    # first and last
    (1, 1, 2, '10'),
    (2, 2, 2, '01'),

    # 7, 8, 9 units selected
    # first and last
    (7, 125, 7, '1011111'),
    (6, 63, 7, '1111110'),
    (8, 253, 8, '10111111'),
    (7, 127, 8, '11111110'),
    (8, 255, 9, '111111110'),

    # add test data selecting multiple
    # units from 15, 16, 17 and 23, 24, 25
]


@pytest.mark.parametrize(
    "mask_x, mask_y, length, expected_bitmask",
    create_bitmask_testdata
)
def test_create_bitmask(mask_x, mask_y, length, expected_bitmask):
    bitmask = bin(mask_y)[2:]

    ceil = math.ceil(len(bitmask)/8)
    if len(bitmask) % 8 != 0:
        bitmask = bitmask.rjust(ceil * 8, '0')

    bitmask_sects = []
    for i in range(0, ceil + 1):
        section = bitmask[8 * i:(8 * i) + 8]
        bitmask_sects.append(section[::-1])

    final_bitmask = ''.join(bitmask_sects)

    if len(final_bitmask) > length:
        final_bitmask = final_bitmask[:length]
    else:
        final_bitmask = final_bitmask.ljust(length, '0')

    assert final_bitmask == expected_bitmask
