class Game:
    def __init__(self, players, game_map, played_at, game_length, events, protocol, gamedata):
        self.players = players
        self.map = game_map
        self.played_at = played_at
        self.game_length = game_length
        self.winner = None
        self.events = events
        self.state = []
        self.timeline = []
        self.engagements = []
        self.protocol = protocol
        self.gamedata = gamedata
