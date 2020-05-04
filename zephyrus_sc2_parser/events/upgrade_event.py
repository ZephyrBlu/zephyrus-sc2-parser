from zephyrus_sc2_parser.events.base_event import BaseEvent


class UpgradeEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        player = self.player
        event = self.event
        upgrades = self.game.gamedata['upgrades']

        if event['m_upgradeTypeName'].decode('utf-8') in upgrades[player.race]:
            player.upgrades.append(event['m_upgradeTypeName'].decode('utf-8'))
