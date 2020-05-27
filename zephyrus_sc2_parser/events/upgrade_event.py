from zephyrus_sc2_parser.events.base_event import BaseEvent


class UpgradeEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        player = self.player
        event = self.event
        upgrades = self.game.gamedata['upgrades']

        lowercase_upgrades = {
            'zerglingmovementspeed': 'ZerglingMovementSpeed',
            'zerglingattackspeed': 'ZerglingAttackSpeed',
            'overlordspeed': 'OverlordSpeed',
        }

        upgrade_name = None
        if event['m_upgradeTypeName'].decode('utf-8') in upgrades[player.race]:
            upgrade_name = event['m_upgradeTypeName'].decode('utf-8')
        elif event['m_upgradeTypeName'].decode('utf-8') in lowercase_upgrades:
            upgrade_name = lowercase_upgrades[event['m_upgradeTypeName'].decode('utf-8')]

        if upgrade_name:
            player.upgrades.append(upgrade_name)
