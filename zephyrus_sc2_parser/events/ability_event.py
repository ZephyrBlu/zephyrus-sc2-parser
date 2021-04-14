import logging
from dataclasses import dataclass
from typing import Optional
from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.dataclasses import Ability, Position
from zephyrus_sc2_parser.game import GameObj

logger = logging.getLogger(__name__)

COMMAND_ABILITIES = {
    'ChronoBoostEnergyCost': 'Nexus',
    'NexusMassRecall': 'Nexus',
    'BatteryOvercharge': 'Nexus',
    'CalldownMULE': 'OrbitalCommand',
    'SupplyDrop': 'OrbitalCommand',
    'ScannerSweep': 'OrbitalCommand',
}


@dataclass(frozen=True)
class ActiveAbility:
    """
    Contains the ability, target object and target position
    of a player's currently active ability
    """
    ability: Ability
    obj: Optional[GameObj]
    target_position: Optional[Position]
    queued: bool


class AbilityEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

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

    def _handle_inject_ability(self, ability_obj):
        player = self.player
        gameloop = self.gameloop

        logger.debug('Inject ability detected')

        # ~1sec
        if not ability_obj.abilities_used:
            ability_obj.abilities_used.append((
                player.active_ability.ability,
                player.active_ability.obj,
                gameloop,
            ))
        elif (gameloop - ability_obj.abilities_used[-1][-1]) > 22 or player.active_ability.target_position:
            ability_obj.abilities_used.append((
                player.active_ability.ability,
                player.active_ability.obj,
                gameloop,
            ))

    def _handle_command_ability(self, ability_name):
        player = self.player
        gameloop = self.gameloop

        logger.debug('Command ability detected')
        ability_buildings = []

        for obj in player.objects.values():
            if obj.name == COMMAND_ABILITIES[ability_name]:
                current_obj_energy = obj.calc_energy(gameloop)
                # abilities cost 50 energy to use
                # if <50 energy the building is not available to cast
                if current_obj_energy and current_obj_energy >= 50:
                    ability_buildings.append(obj)

        # need to check ability_buildings because events can show up repeatedly
        # although only 1 is executed. To tell exactly which one, need to do secondary parsing
        if ability_buildings and player.active_ability.target_position:
            ability_obj = min(
                ability_buildings,
                key=lambda x: x.calc_distance(player.active_ability.target_position),
            )
            ability_obj.abilities_used.append((
                player.active_ability.ability,
                player.active_ability.obj,
                gameloop,
            ))

    def _handle_landing_ability(self, ability_name):
        player = self.player
        gameloop = self.gameloop

        logger.debug('Landing ability detected')
        ability_buildings = []
        # 'Land' is 4 letters, -4 slice removes it and leaves object name
        obj_name = ability_name[:-4]

        for obj in player.objects.values():
            if f'{obj_name}Flying' == obj.name:
                ability_buildings.append(obj)

        # if only 1 building of type, it's easy otherwise
        # we need to calculate a match based on last known positions
        # we assume that the building which was closer to the landing position
        # is the correct building
        ability_obj = min(
            ability_buildings,
            key=lambda x: x.calc_distance(player.active_ability.target_position),
        )
        player.active_ability.ability.target_position = player.active_ability.target_position
        ability_obj.abilities_used.append((
            player.active_ability.ability,
            player.active_ability.obj,
            gameloop,
        ))

    def parse_event(self):
        event = self.event
        player = self.player
        gameloop = self.gameloop
        abilities = self.game.gamedata.abilities

        logger.debug(f'Parsing {self.type} at {gameloop}')

        if not player:
            logger.debug('No player associated with this event')
            return

        logger.debug(f'Player: {player.name} ({player.player_id})')
        logger.debug(f'Active ability: {player.active_ability}')

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
                        target_position = Position(
                            event['m_data']['TargetUnit']['m_snapshotPoint']['x'] / 4096,
                            event['m_data']['TargetUnit']['m_snapshotPoint']['y'] / 4096,
                        )
                    elif 'TargetPoint' in event['m_data']:
                        target_position = Position(
                            event['m_data']['TargetPoint']['x'] / 4096,
                            event['m_data']['TargetPoint']['y'] / 4096,
                        )

                ability_data = abilities[event['m_abil']['m_abilLink']]
                ability = ActiveAbility(
                    Ability(
                        ability_data['ability_name'],
                        ability_data['energy_cost'] if 'energy_cost' in ability_data else None,
                    ),
                    obj,
                    target_position,
                    queued,
                )
            else:
                ability = None
            player.active_ability = ability
            logger.debug(f'New active ability: {player.active_ability}')

        if player.active_ability:
            ability_name = player.active_ability.ability.name
            ability_obj = player.active_ability.obj
            if ability_name == 'SpawnLarva' and ability_obj:
                self._handle_inject_ability(ability_obj)

            # the building the target is closest to is where the ability is used from
            elif ability_name in COMMAND_ABILITIES.keys():
                self._handle_command_ability(ability_name)

            # need to record information about flying/landing buildings for Terran
            elif 'Land' in ability_name:
                self._handle_landing_ability(ability_name)
