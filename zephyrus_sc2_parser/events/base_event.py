import logging

logger = logging.getLogger(__name__)


class BaseEvent:
    def __init__(self, game, event):
        self.game = game
        self.event = event
        self.type = event['_event']
        self.player = self._identify_player(game, event)
        self.gameloop = event['_gameloop']

    def _identify_player(self, game, event):
        no_player = [
            'NNet.Replay.Tracker.SUnitDoneEvent',
            'NNet.Replay.Tracker.SUnitDiedEvent',
            'NNet.Replay.Tracker.SUnitTypeChangeEvent'
        ]
        if event['_event'] in no_player:
            return False

        if game is None:
            logger.warning('Game in event is None')
            return None

        for p_id, player in game.players.items():
            if 'm_controlPlayerId' in event:
                if p_id == event['m_controlPlayerId']:
                    return player
            elif 'm_playerId' in event:
                if p_id == event['m_playerId']:
                    return player
            elif '_userid' in event:
                if player.user_id == event['_userid']['m_userId']:
                    return player
            else:
                return None
