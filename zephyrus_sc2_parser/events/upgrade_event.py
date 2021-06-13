import logging
from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.dataclasses import Upgrade

logger = logging.getLogger(__name__)


class UpgradeEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        event = self.event
        player = self.player
        gameloop = self.gameloop
        upgrades = self.game.gamedata.upgrades

        logger.debug(f'Parsing {self.type} at {gameloop}')
        logger.debug(f'Player: {player.name} ({player.player_id})')

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
            logger.debug(f'Adding upgrade: {upgrade_name} to player')
            upgrade_research_time = upgrades[player.race][upgrade_name]['research_time']
            upgrade_start_time = gameloop - upgrade_research_time
            player.upgrades.append(Upgrade(upgrade_name, upgrade_start_time, gameloop))
        else:
            logger.warning(f'Unknown upgrade: {event["m_upgradeTypeName"].decode("utf-8")}')
