from datetime import datetime
from typing import Dict, Optional, List, Tuple
from zephyrus_sc2_parser.dataclasses import Map, GameData
from zephyrus_sc2_parser.game.player import Player


class Game:
    """Contains general information about the game"""
    def __init__(self, players, game_map, played_at, game_length, events, protocol, gamedata):
        self.players: Dict[int, Player] = players
        self.map: Map = game_map
        self.played_at: datetime = played_at
        self.game_length: int = game_length
        self.winner: Optional[bool] = None
        self.events: List[Dict] = events
        self.state: List[Tuple] = []
        self.timeline: List[Dict[int, Dict]] = []
        self.engagements: List = []
        self.protocol: int = protocol
        self.gamedata: GameData = gamedata
