from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.game.game_obj import GameObj
from zephyrus_sc2_parser.gamedata.unit_data import units
from zephyrus_sc2_parser.gamedata.building_data import buildings
import copy


class ObjectEvent(BaseEvent):
    def __init__(self, protocol, summary_stats, *args):
        super().__init__(*args)
        self.protocol = protocol
        self.summary_stats = summary_stats

    def _get_or_create_game_object(self):
        event = self.event
        unit_tag_index = self.event['m_unitTagIndex']
        unit_tag_recycle = self.event['m_unitTagRecycle']
        game_id = self.protocol.unit_tag(unit_tag_index, unit_tag_recycle)

        if self.player is False:
            for p in self.game.players:
                if game_id in p.objects:
                    self.player = p
                    return self.player.objects[game_id]

        player = self.player

        if player:
            if game_id in player.objects:
                return player.objects[game_id]

            obj_name = event['m_unitTypeName'].decode('utf-8')
            if obj_name in units[player.race]:
                obj = units[player.race][obj_name]
            elif obj_name in buildings[player.race]:
                obj = buildings[player.race][obj_name]
            else:
                return None

            new_game_obj = GameObj(
                obj_name,
                obj['obj_id'],
                game_id,
                unit_tag_index,
                obj['priority'],
                obj['mineral_cost'],
                obj['gas_cost']
            )

            for value in obj['type']:
                new_game_obj.type.append(value)

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
        for group_num, index in obj.control_groups.items():
            if group_num in self.player.control_groups:
                ctrl_group = self.player.control_groups[group_num]

                # print(obj)
                # print(group_num, index)
                # print(ctrl_group)
                # print(self.event)
                # remove = ctrl_group[index]
                # print(f'{obj.name} being updated')
                # print(f'{remove} deleted @: {index}')
                if len(ctrl_group) - 1 >= index:
                    del ctrl_group[index]

                ctrl_group.append(obj)
                ctrl_group.sort(key=lambda x: x.tag)

                for index, obj in enumerate(ctrl_group):
                    obj.control_groups[group_num] = index
                # print(self.event)
                # print()

    def parse_event(self):
        obj = self._get_or_create_game_object()
        player = self.player
        event = self.event
        summary_stats = self.summary_stats
        protocol = self.protocol
        gameloop = self.gameloop

        if not obj or not player:
            return None

        if self.type == 'NNet.Replay.Tracker.SUnitInitEvent':
            obj.status = 'in_progress'

        elif self.type == 'NNet.Replay.Tracker.SUnitDoneEvent':
            obj.birth_time = gameloop
            obj.status = 'live'

        elif self.type == 'NNet.Replay.Tracker.SUnitBornEvent':
            obj.birth_time = gameloop
            obj.status = 'live'

            if 'worker' in obj.type:
                summary_stats['workers_produced'][player.player_id] += 1

        elif self.type == 'NNet.Replay.Tracker.SUnitDiedEvent':
            obj.status = 'died'
            obj.death_time = gameloop

            obj_killer_tag = event['m_killerUnitTagIndex']
            obj_killer_recycle = event['m_killerUnitTagRecycle']

            if obj_killer_tag and obj_killer_recycle:
                obj_killer_id = protocol.unit_tag(obj_killer_tag, obj_killer_recycle)
                for p in self.game.players:
                    if obj_killer_id in p.objects:
                        obj.killed_by = p.objects[obj_killer_id]

        elif self.type == 'NNet.Replay.Tracker.SUnitTypeChangeEvent':
            new_obj_name = event['m_unitTypeName'].decode('utf-8')
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

            # organised in alphabetically sorted order
            morph_units = [
                ['BanelingCocoon', 'Zergling'],
                ['Baneling', 'BanelingCocoon'],
                ['OverlordCocoon', 'Overseer'],
                ['OverlordTransport', 'TransportOverlordCocoon'],
                ['Ravager', 'RavagerCocoon'],
                ['LurkerMP', 'LurkerMPEgg'],
                ['BroodLord', 'BroodLordCocoon']
            ]

            if sorted([old_name, new_obj_name]) in morph_units:
                obj.morph_time = gameloop

            if 'Egg' in old_name or 'Cocoon' in old_name:
                self._update_obj_group_info(obj)
