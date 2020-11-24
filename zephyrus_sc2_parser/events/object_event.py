import copy
import logging
from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.game.game_obj import GameObj

logger = logging.getLogger(__name__)


class ObjectEvent(BaseEvent):
    def __init__(self, protocol, summary_stats, *args):
        super().__init__(*args)
        self.protocol = protocol
        self.summary_stats = summary_stats

    def _get_or_create_game_object(self):
        units = self.game.gamedata['units']
        buildings = self.game.gamedata['buildings']

        event = self.event
        unit_tag_index = self.event['m_unitTagIndex']
        unit_tag_recycle = self.event['m_unitTagRecycle']
        game_id = self.protocol.unit_tag(unit_tag_index, unit_tag_recycle)

        # obj_name = None
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
            obj['priority'],
            obj['mineral_cost'],
            obj['gas_cost']
        )

        if 'energy' in obj:
            new_game_obj.energy = obj['energy']

        if 'cooldown' in obj:
            new_game_obj.cooldown = obj['cooldown']

        for value in obj['type']:
            new_game_obj.obj_type.append(value)

            if value == 'unit':
                new_game_obj.supply = obj['supply']
            elif value == 'building':
                new_game_obj.queue = []
            elif value == 'supply':
                if obj_name == 'Overlord' or 'Overseer':
                    new_game_obj.supply_provided = 8
                else:
                    new_game_obj.supply_provided = obj['supply']

        player.objects[game_id] = new_game_obj
        return new_game_obj

    def _update_obj_group_info(self, obj):
        logger.debug(f'Updating control group references in object {obj}')
        for group_num, index in obj.control_groups.items():
            logger.debug(f'Object at position {index} in control group {group_num}')
            if group_num not in self.player.control_groups:
                logger.warning(f'Object contains reference to control group {group_num}, but no such group exists for player {player.name} ({player.player_id})')
                return

            ctrl_group = self.player.control_groups[group_num]

            logger.debug(f'Control group length: {len(ctrl_group)}')

            # print(obj)
            # print(group_num, index)
            # print(ctrl_group)
            # print(self.event)
            # remove = ctrl_group[index]
            # print(f'{obj.name} being updated')
            # print(f'{remove} deleted @: {index}')
            if len(ctrl_group) - 1 >= index:
                logger.debug(f'Removed object {ctrl_group[index]} from control group {group_num}')
                del ctrl_group[index]
            else:
                logger.warning(f'Object position ({index}) is greater outside bounds of control group ({len(ctrl_group)})')

            ctrl_group.append(obj)
            ctrl_group.sort(key=lambda x: x.tag)
            logger.debug(f'Added object {obj} to control group {group_num}')

            # re-order control group after adding new object
            for index, obj in enumerate(ctrl_group):
                obj.control_groups[group_num] = index
            logger.debug('Updated control group references in objects')
            # print(self.event)
            # print()

    def parse_event(self):
        units = self.game.gamedata['units']
        buildings = self.game.gamedata['buildings']

        logger.debug(f'Parsing {self.event_type} at {self.gameloop}')

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

        if self.event_type == 'NNet.Replay.Tracker.SUnitInitEvent':
            obj.status = 'in_progress'
            obj.init_time = gameloop
            obj.position = {
                'x': event['m_x'],
                'y': event['m_y'],
            }
            logger.debug(f'Updated object status to: {obj.status}')
            logger.debug(f'Updated object init_time to: {obj.init_time}')
            logger.debug(f'Updated object position to: {obj.position}')

            if player.warpgate_cooldowns and 'unit' in obj.obj_type:
                first_cooldown = player.warpgate_cooldowns[0]
                time_past_cooldown = gameloop - (first_cooldown[0] + first_cooldown[1])

                if time_past_cooldown >= 0:
                    player.warpgate_cooldowns.pop(0)
                    player.warpgate_efficiency = (
                        player.warpgate_efficiency[0] + first_cooldown[1],
                        player.warpgate_efficiency[1] + time_past_cooldown
                    )

            # only warped in units generate this event
            if 'unit' in obj.obj_type and obj.name != 'Archon' and obj.name != 'OracleStasisTrap':
                player.warpgate_cooldowns.append((gameloop, obj.cooldown))
                player.warpgate_cooldowns.sort(key=lambda x: x[0] + x[1])

                warpgate_count = 0
                for obj_id, obj in player.objects.items():
                    if obj.name == 'WarpGate':
                        warpgate_count += 1

                while len(player.warpgate_cooldowns) > warpgate_count:
                    player.warpgate_cooldowns.pop()

        elif self.event_type == 'NNet.Replay.Tracker.SUnitDoneEvent':
            obj.birth_time = gameloop
            obj.status = 'live'
            logger.debug(f'Updated object birth_time to: {obj.birth_time}')
            logger.debug(f'Updated object status to: {obj.status}')

        elif self.event_type == 'NNet.Replay.Tracker.SUnitBornEvent':
            obj.birth_time = gameloop
            obj.status = 'live'

            logger.debug(f'Updated object birth_time to: {obj.birth_time}')
            logger.debug(f'Updated object status to: {obj.status}')

            if 'worker' in obj.obj_type:
                summary_stats['workers_produced'][player.player_id] += 1

            if not obj.position:
                obj.position = {
                    'x': event['m_x'],
                    'y': event['m_y'],
                }
                logger.debug(f'Updated object position to: {obj.position}')

        elif self.event_type == 'NNet.Replay.Tracker.SUnitDiedEvent':
            obj.status = 'died'
            obj.death_time = gameloop

            logger.debug(f'Updated object status to: {obj.status}')
            logger.debug(f'Updated object death_time to: {obj.death_time}')

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

        elif self.event_type == 'NNet.Replay.Tracker.SUnitTypeChangeEvent':
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
            # add Archons to morph units
            # stop HTs morhping into Archons being counted as dead HTs
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

            if 'Egg' in old_name or 'Cocoon' in old_name:
                self._update_obj_group_info(obj)

        # player.calc_supply()
