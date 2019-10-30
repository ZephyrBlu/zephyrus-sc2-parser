import pytest


validate_player_rating_testdata = [
    ([{'m_scaledRating': 1000}, {'m_scaledRating': 1000}], True),
    ([{'m_scaledRating': 0}, {'m_scaledRating': 1000}], True),
    ([{'m_scaledRating': -1}, {'m_scaledRating': 1000}], True),
    ([{'m_scaledRating': None}, {'m_scaledRating': 1000}], False),
    ([{'m_scaledRating': 'abc'}, {'m_scaledRating': 1000}], False),
    ([{'m_scaledRating': 1000}, {'m_scaledRating': 0}], True),
    ([{'m_scaledRating': 1000}, {'m_scaledRating': -1}], True),
    ([{'m_scaledRating': 1000}, {'m_scaledRating': None}], False),
    ([{'m_scaledRating': 1000}, {'m_scaledRating': 'abc'}], False),
]

@pytest.mark.parametrize("mmr_data, expected", validate_player_rating_testdata)
def test_summary_stats_get_player_rating(mmr_data, expected):

    ranked_game = None

    player1_mmr = mmr_data[0]['m_scaledRating']
    player2_mmr = mmr_data[1]['m_scaledRating']

    if type(player1_mmr) is not int or type(player2_mmr) is not int:
        ranked_game = False

        if not player1_mmr or not player2_mmr:
            assert ranked_game == expected, "Expected result of None MMR value to be False"
            print("A player does not have a MMR value")

        elif type(player1_mmr) is str or type(player2_mmr) is str:
            assert ranked_game == expected, "Expected result of string MMR value to be False"
            print("A player has a string as their MMR value")

        else:
            assert ranked_game == expected, "Expected result of invalid MMR value to be False"
            print("A player has an invalid MMR value")

    elif player1_mmr < 0 or player2_mmr < 0:
        ranked_game = True

        assert ranked_game == expected, "Expected result of negative MMR value to be True"
        print("A player has a negative MMR value (Playing unranked)")

    else:
        ranked_game = True

        assert ranked_game == expected, "Expected result of valid MMR value to be True"
        print("Both players have valid MMR values")


parse_replay_testdata = [
    (ValueError, 'unreadable header'),
    (ImportError, 'unsupported protocol'),
    (KeyError, 'unreadable file info'),    
]

# get real files that cause these failures for testing?
@pytest.mark.parametrize("exception, expected", parse_replay_testdata)
def test_parse_replay_file_setup(exception, expected):
    if exception is ValueError:
        assert expected == 'unreadable header'
        print("ValueError caused by unreadable header")
    elif exception is ImportError:
        assert expected == 'unsupported protocol'
        print("ImportError caused by unsupported protocol")
    elif exception is KeyError:
        assert expected == 'unreadable file info'
        print("KeyError caused by unreadable file info")
