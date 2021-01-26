class Sc2ParserException(Exception):
    """Base class for SC2 Parser exceptions."""
    pass


class MissingMmrError(Sc2ParserException):
    """
    Occurs when a player's MMR is missing and
    a replay is not being parsed in local mode
    """
    pass


class ReplayDecodeError(Sc2ParserException):
    """
    Occurs when a replay is unable to be decoded
    using s2protocol

    Can be due to any of the following:
    - ValueError: Unreadable header
    - ImportError: Unsupported protocol
    - KeyError: Unreadable file info
    """
    pass


class PlayerCountError(Sc2ParserException):
    """
    Occurs when there are not exactly 2 players in the replay
    """
    pass


class GameLengthNotFoundError(Sc2ParserException):
    """
    Occurs when a game ends without PlayerLeave events. I have no idea why this happens
    """
    pass
