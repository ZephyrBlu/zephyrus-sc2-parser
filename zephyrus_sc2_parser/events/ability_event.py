import logging
from zephyrus_sc2_parser.events.base_event import BaseEvent

logger = logging.getLogger(__name__)


class AbilityEvent(BaseEvent):
    def __init__(self, summary_stats, *args):
        super().__init__(*args)
        self.summary_stats = summary_stats

    def _get_target_object(self):
        event = self.event

        if 'None' in event['m_data'] or 'TargetUnit' not in event['m_data']:
            logger.debug('No target object')
            return None

        unit_game_id = event['m_data']['TargetUnit']['m_tag']

        for obj_id, obj in self.player.objects.items():
            if obj.tag == event['m_data']['TargetUnit']['m_snapshotUnitLink']:
                break

        if unit_game_id in self.player.objects:
            logger.debug('Found target object')
            return self.player.objects[unit_game_id]

        logger.debug('Target object is not in player objects')
        return None

    def parse_event(self):
        event = self.event
        player = self.player
        gameloop = self.gameloop
        summary_stats = self.summary_stats
        abilities = self.game.gamedata['abilities']

        logger.debug(f'Parsing {self.type} at {gameloop}')

        if not player:
            logger.debug('No player associated with this event')
            return

        logger.debug(f'Player: {player.name} ({player.player_id})')
        logger.debug(f'Active ability: {player.active_ability}')

        command_abilities = {
            'ChronoBoostEnergyCost': 'Nexus',
            'NexusMassRecall': 'Nexus',
            'CalldownMULE': 'OrbitalCommand',
            'SupplyDrop': 'OrbitalCommand',
            'ScannerSweep': 'OrbitalCommand',
        }

        if self.type == 'NNet.Game.SCmdEvent':
            if event['m_abil'] and event['m_abil']['m_abilLink'] and event['m_abil']['m_abilLink'] in abilities and type(event['m_abil']['m_abilCmdIndex']) is int:
                obj = self._get_target_object()
                queued = False
                if 'm_cmdFlags' in event:
                    bitwise = event['m_cmdFlags'] & 2
                    if bitwise == 2:
                        queued = True

                target_position = None
                if 'm_data' in event:
                    if 'TargetUnit' in event['m_data']:
                        target_position = event['m_data']['TargetUnit']['m_snapshotPoint']
                    elif 'TargetPoint' in event['m_data']:
                        target_position = event['m_data']['TargetPoint']

                ability = (
                    abilities[event['m_abil']['m_abilLink']],
                    obj,
                    target_position,
                    queued,
                )
            else:
                ability = None
            player.active_ability = ability
            logger.debug(f'New active ability: {player.active_ability}')

            if player.active_ability:
                ability_name = player.active_ability[0]['ability_name']
                if ability_name == 'SpawnLarva' and obj:
                    # ~1sec
                    if not obj.abilities_used:
                        obj.abilities_used.append((player.active_ability[0], player.active_ability[1], gameloop))
                    elif (gameloop - obj.abilities_used[-1][-1]) > 22 or player.active_ability[2]:
                        obj.abilities_used.append((player.active_ability[0], player.active_ability[1], gameloop))

                # the building the target is closest to is where the ability is used from
                elif ability_name in command_abilities.keys():
                    logger.debug('Command ability detected')
                    ability_buildings = []

                    for obj in player.objects.values():
                        if obj.name == command_abilities[ability_name]:
                            current_obj_energy = obj.calc_energy(gameloop)
                            # abilities cost 50 energy to use
                            # if <50 energy the building is not available to cast
                            if current_obj_energy and current_obj_energy >= 50:
                                ability_buildings.append(obj)

                    if ability_buildings and player.active_ability[2]:
                        ability_obj = min(ability_buildings, key=lambda x: x.calc_distance(player.active_ability[2]))
                        ability_obj.abilities_used.append((player.active_ability[0], player.active_ability[1], gameloop))
        else:
            if player.active_ability:
                ability_name = player.active_ability[0]['ability_name']
                if ability_name in command_abilities.keys():
                    logger.debug('Command ability detected')
                    ability_buildings = []

                    for obj in player.objects.values():
                        if obj.name == command_abilities[ability_name]:
                            current_obj_energy = obj.calc_energy(gameloop)
                            # abilities cost 50 energy to use
                            # if <50 energy the building is not available to cast
                            if current_obj_energy and current_obj_energy >= 50:
                                ability_buildings.append(obj)

                    if ability_buildings and player.active_ability[2]:
                        ability_obj = min(ability_buildings, key=lambda x: x.calc_distance(player.active_ability[2]))
                        ability_obj.abilities_used.append((player.active_ability[0], player.active_ability[1], gameloop))

        return summary_stats
