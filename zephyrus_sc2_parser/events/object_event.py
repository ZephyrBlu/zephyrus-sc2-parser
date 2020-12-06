import copy
import logging
from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.game import GameObj
from zephyrus_sc2_parser.dataclasses import Position

logger = logging.getLogger(__name__)


class ObjectEvent(BaseEvent):
    def __init__(self, protocol, summary_stats, *args):
        super().__init__(*args)
        self.protocol = protocol
        self.summary_stats = summary_stats

    def _get_or_create_game_object(self):
        units = self.game.gamedata.units
        buildings = self.game.gamedata.buildings

        event = self.event
        unit_tag_index = self.event['m_unitTagIndex']
        unit_tag_recycle = self.event['m_unitTagRecycle']
        game_id = self.protocol.unit_tag(unit_tag_index, unit_tag_recycle)

        obj_name = None
        if 'm_unitTypeName' in event:
            obj_name = event['m_unitTypeName'].decode('utf-8')
            logger.debug(f'Event object name: {obj_name}, ({game_id})')

        if self.player is False:
            logger.debug('Event does not contain player information. Checking players for event object')
            for p in self.game.players.values():
                if game_id in p.objects:
                    logger.debug('Found event object in player. Setting player and returning event object')
                    self.player = p
                    return self.player.objects[game_id]

        player = self.player

        if not player:
            return None

        if game_id in player.objects:
            logger.debug('Found event object in player. Returning event object')
            return player.objects[game_id]

        if obj_name in units[player.race]:
            obj = units[player.race][obj_name]
        elif obj_name in buildings[player.race]:
            obj = buildings[player.race][obj_name]
        else:
            return None

        logger.debug('Creating new object')
        new_game_obj = GameObj(
            obj_name,
            obj['obj_id'],
            game_id,
            unit_tag_index,
            unit_tag_recycle,
            obj['priority'],
            obj['mineral_cost'],
            obj['gas_cost']
        )

        if 'energy' in obj:
            new_game_obj.energy = obj['energy']

        if 'cooldown' in obj:
            new_game_obj.cooldown = obj['cooldown']

        for value in obj['type']:
            # convert to uppercase for comparisons
            new_game_obj.type.append(value.upper())

            if value == GameObj.UNIT:
                new_game_obj.supply = obj['supply']
            elif value == GameObj.BUILDING:
                new_game_obj.queue = []
            elif value == GameObj.SUPPLY:
                if obj_name == 'Overlord' or 'Overseer':
                    new_game_obj.supply_provided = 8
                else:
                    new_game_obj.supply_provided = obj['supply']

        player.objects[game_id] = new_game_obj
        return new_game_obj

    def parse_event(self):
        units = self.game.gamedata.units
        buildings = self.game.gamedata.buildings

        logger.debug(f'Parsing {self.type} at {self.gameloop}')

        # _get_or_create_game_object can alter self.player, so must be executed first
        obj = self._get_or_create_game_object()

        event = self.event
        player = self.player
        gameloop = self.gameloop

        if not player:
            logger.warning('Missing player in event')
        else:
            logger.debug(f'Player: {player.name} ({player.player_id})')

        if not obj:
            logger.warning('Missing object in event')
        else:
            logger.debug(f'Object: {obj}')

        if not obj or not player:
            return None

        summary_stats = self.summary_stats
        protocol = self.protocol

        if self.type == 'NNet.Replay.Tracker.SUnitInitEvent':
            obj.status = GameObj.IN_PROGRESS
            obj.init_time = gameloop
            obj.position = Position(
                event['m_x'],
                event['m_y'],
            )
            logger.debug(f'Updated object status to: {obj.status}')
            logger.debug(f'Updated object init_time to: {obj.init_time}')
            logger.debug(f'Updated object position to: {obj.position}')

            if player.warpgate_cooldowns and GameObj.UNIT in obj.type:
                first_cooldown = player.warpgate_cooldowns[0]
                time_past_cooldown = gameloop - (first_cooldown[0] + first_cooldown[1])

                if time_past_cooldown >= 0:
                    player.warpgate_cooldowns.pop(0)
                    player.warpgate_efficiency = (
                        player.warpgate_efficiency[0] + first_cooldown[1],
                        player.warpgate_efficiency[1] + time_past_cooldown
                    )

            # only warped in units generate this event
            if GameObj.UNIT in obj.type and obj.name != 'Archon' and obj.name != 'OracleStasisTrap':
                player.warpgate_cooldowns.append((gameloop, obj.cooldown))
                player.warpgate_cooldowns.sort(key=lambda x: x[0] + x[1])

                warpgate_count = 0
                for obj_id, obj in player.objects.items():
                    if obj.name == 'WarpGate':
                        warpgate_count += 1

                while len(player.warpgate_cooldowns) > warpgate_count:
                    player.warpgate_cooldowns.pop()

        elif self.type == 'NNet.Replay.Tracker.SUnitDoneEvent':
            obj.birth_time = gameloop
            obj.status = GameObj.LIVE

            logger.debug(f'Updated object birth_time to: {obj.birth_time}')
            logger.debug(f'Updated object status to: {obj.status}')

        elif self.type == 'NNet.Replay.Tracker.SUnitBornEvent':
            obj.birth_time = gameloop
            obj.status = GameObj.LIVE

            logger.debug(f'Updated object birth_time to: {obj.birth_time}')
            logger.debug(f'Updated object status to: {obj.status}')

            if GameObj.WORKER in obj.type:
                summary_stats['workers_produced'][player.player_id] += 1

            if not obj.position:
                obj.position = Position(
                    event['m_x'],
                    event['m_y'],
                )
                logger.debug(f'Updated object position to: {obj.position}')

        elif self.type == 'NNet.Replay.Tracker.SUnitDiedEvent':
            obj.status = GameObj.DIED
            obj.death_time = gameloop

            logger.debug(f'Updated object status to: {obj.status}')
            logger.debug(f'Updated object death_time to: {obj.death_time}')

            # # control groups aren't automatically updated when an object dies
            # # so we need to do it manually
            # if obj.control_groups:
            #     for ctrl_group, index in obj.control_groups.items():
            #         # remove reference to control group
            #         del player.control_groups[ctrl_group][index]

            #         # from ControlGroupEvent, _set_obj_group_info
            #         logger.debug(f'Binding control group {ctrl_group} to objects')
            #         for index, obj in enumerate(player.control_groups[ctrl_group]):
            #             obj.control_groups[ctrl_group] = index
            #             logger.debug(f'Binding control group {ctrl_group} to {obj} at position {index}')

            if obj.name == 'WarpGate' and player.warpgate_cooldowns:
                player.warpgate_cooldowns.pop()

            obj_killer_tag = event['m_killerUnitTagIndex']
            obj_killer_recycle = event['m_killerUnitTagRecycle']

            if obj_killer_tag and obj_killer_recycle:
                obj_killer_id = protocol.unit_tag(obj_killer_tag, obj_killer_recycle)
                for p in self.game.players.values():
                    if obj_killer_id in p.objects:
                        obj.killed_by = p.objects[obj_killer_id]
                        logger.debug(f'Object killed by {obj.killed_by}')

        elif self.type == 'NNet.Replay.Tracker.SUnitTypeChangeEvent':
            new_obj_name = event['m_unitTypeName'].decode('utf-8')
            logger.debug(f'New object name: {new_obj_name}')
            if new_obj_name in units[player.race]:
                new_obj_info = units[player.race][new_obj_name]
            elif new_obj_name in buildings[player.race]:
                new_obj_info = buildings[player.race][new_obj_name]
            else:
                return

            obj_tag = event['m_unitTagIndex']
            obj_recycle = event['m_unitTagRecycle']
            obj_game_id = protocol.unit_tag(obj_tag, obj_recycle)

            obj = player.objects[obj_game_id]
            old_name = copy.copy(obj.name)

            obj.name = new_obj_name
            obj.obj_id = new_obj_info['obj_id']
            obj.game_id = obj_game_id
            obj.tag = obj_tag
            obj.priority = new_obj_info['priority']
            obj.mineral_cost = new_obj_info['mineral_cost']
            obj.gas_cost = new_obj_info['gas_cost']
            obj.supply = new_obj_info['supply']

            if 'energy' in new_obj_info:
                obj.energy = new_obj_info['energy']

            # organised in alphabetically sorted order
            morph_units = [
                ['BanelingCocoon', 'Zergling'],
                ['Baneling', 'BanelingCocoon'],
                ['OverlordCocoon', 'Overseer'],
                ['OverlordTransport', 'TransportOverlordCocoon'],
                ['Ravager', 'RavagerCocoon'],
                ['LurkerMP', 'LurkerMPEgg'],
                ['BroodLord', 'BroodLordCocoon'],
                ['CommandCenter', 'OrbitalCommand'],
            ]

            if sorted([old_name, new_obj_name]) in morph_units:
                obj.morph_time = gameloop
