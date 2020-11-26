class MissingMmrError(Exception):
    """
    Occurs when a player's MMR is missing and
    a replay is not being parsed in local mode
    """
    pass


class ReplayDecodeError(Exception):
    """
    Occurs when a replay is unable to be decoded
    using s2protocol

    Can be due to any of the following:
    - ValueError: Unreadable header
    - ImportError: Unsupported protocol
    - KeyError: Unreadable file info
    """
    pass


class PlayerCountError(Exception):
    """
    Occurs when there are not exactly 2 players in the replay
    """
    pass


class GameLengthNotFoundError(Exception):
    """
    """
    pass
