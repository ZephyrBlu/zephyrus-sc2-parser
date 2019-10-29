from zephyrus_sc2_parser.game.perception_action_cycle import PerceptionActionCycle
from zephyrus_sc2_parser.game.game_obj import GameObj
from zephyrus_sc2_parser.gamedata.unit_data import units
from zephyrus_sc2_parser.gamedata.building_data import buildings
import math
import copy


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
            return None

        for player in game.players:
            if 'm_controlPlayerId' in event:
                if player.player_id == event['m_controlPlayerId']:
                    return player
            elif 'm_playerId' in event:
                if player.player_id == event['m_playerId']:
                    return player
            elif '_userid' in event:
                if player.user_id == event['_userid']['m_userId']:
                    return player
            else:
                return None


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
            ctrl_group = self.player.control_groups[group_num]

            # print(obj)
            # print(group_num, index)
            # print(ctrl_group)
            # print(self.event)
            # remove = ctrl_group[index]
            # print(f'{obj.name} being updated')
            # print(f'{remove} deleted @: {index}')
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
        gameloop = event['_gameloop']

        if not obj:
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

            if 'Egg' in old_name or 'Cocoon' in old_name:
                self._update_obj_group_info(obj)


class AbilityEvent(BaseEvent):
    def __init__(self, summary_stats, *args):
        super().__init__(*args)
        self.summary_stats = summary_stats

    def parse_event(self):
        player = self.player
        event = self.event
        summary_stats = self.summary_stats

        if self.type == 'NNet.Game.SCmdEvent':
            if event['m_abil']:
                if event['m_abil']['m_abilLink'] and event['m_abil']['m_abilCmdIndex']:
                    ability = (
                        event['m_abil']['m_abilLink'],
                        event['m_abil']['m_abilCmdIndex']
                    )
                else:
                    ability = None
                player.active_ability = ability

                if player.active_ability and player.active_ability[0] == 183:
                    summary_stats['inject_count'][player.player_id] += 1
        else:
            if player.active_ability and player.active_ability[0] == 183:
                summary_stats['inject_count'][player.player_id] += 1

        return summary_stats


class SelectionEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def _add_to_selection(self, ctrl_group_num, new_obj_ids):
        if ctrl_group_num:
            selection = self.player.control_groups[ctrl_group_num]
        else:
            selection = self.player.current_selection

        for obj_game_id in new_obj_ids:
            if obj_game_id not in self.player.objects:
                return

        for obj_game_id in new_obj_ids:
            obj = self.player.objects[obj_game_id]
            selection.append(obj)

        selection.sort(key=lambda x: x.tag)

    def _handle_zero_indices(self, ctrl_group_num, *, selection_type):
        """
        new: Clear the current selection and create a new one
        containing the newly selected units/buildings

        sub: Sub-select the units/buildings in the positions
        given by 'm_removeMask' from the current selection
        """
        player = self.player
        event = self.event

        if selection_type == 'new':
            if ctrl_group_num:
                player.control_groups[ctrl_group_num] = []
                selection = player.control_groups[ctrl_group_num]
            else:
                player.current_selection = []
                selection = player.current_selection

            new_game_ids = event['m_delta']['m_addUnitTags']

            for obj_game_id in new_game_ids:
                if obj_game_id in player.objects:
                    selection.append(player.objects[obj_game_id])
            selection.sort(key=lambda x: x.tag)

        elif selection_type == 'sub':
            if ctrl_group_num:
                selection = player.control_groups[ctrl_group_num]
            else:
                selection = player.current_selection

            selection_indices = event['m_delta']['m_removeMask']['ZeroIndices']

            for i in range(len(selection) - 1, -1, -1):
                if i not in selection_indices:
                    del selection[i]

    def _handle_one_indices(self, ctrl_group_num, *, selection_type):
        """
        new: Remove the unit/building in the position given
        by 'm_removeMask' from the current selection.

        sub: Remove the units in the position given
        by 'm_removeMask' from the current selection and add
        the new units.
        """
        player = self.player
        event = self.event
        selection_indices = event['m_delta']['m_removeMask']['OneIndices']

        if ctrl_group_num:
            selection = player.control_groups[ctrl_group_num]
        else:
            selection = player.current_selection

        if selection_type == 'new':
            new_game_ids = event['m_delta']['m_addUnitTags']

            # reverse order of current selection so object removals
            # don't affect future removals
            for i in range(len(selection) - 1, -1, -1):
                if i in selection_indices:
                    del selection[i]
            self._add_to_selection(ctrl_group_num, new_game_ids)

        elif selection_type == 'sub':
            # reverse order of current selection so object removals
            # don't affect future removals
            for i in range(len(selection) - 1, -1, -1):
                if i in selection_indices:
                    del selection[i]

    def _create_bitmask(self, mask_x, mask_y, length):
        bitmask = bin(mask_y)[2:]

        ceil = math.ceil(len(bitmask)/8)
        if len(bitmask) % 8 != 0:
            bitmask = bitmask.rjust(ceil * 8, '0')

        bitmask_sects = []
        for i in range(0, ceil + 1):
            section = bitmask[8 * i:(8 * i) + 8]
            bitmask_sects.append(section[::-1])

        final_bitmask = ''.join(bitmask_sects)

        if len(final_bitmask) > length:
            final_bitmask = final_bitmask[:length + 1]
        else:
            final_bitmask = final_bitmask.ljust(length, '0')

        return final_bitmask

    def _handle_mask(self, ctrl_group_num, *, selection_type):
        """
        new:

        sub:
        """
        if selection_type == 'new':
            return

        player = self.player
        event = self.event
        mask_x = event['m_delta']['m_removeMask']['Mask'][0]
        mask_y = event['m_delta']['m_removeMask']['Mask'][1]

        if ctrl_group_num:
            selection = player.control_groups[ctrl_group_num]
        else:
            selection = player.current_selection

        length = len(selection)

        bitmask = self._create_bitmask(mask_x, mask_y, length)

        for i in range(length - 1, -1, -1):
            if bitmask[i] == '1':
                del selection[i]

    def _handle_none(self, ctrl_group_num, *, selection_type):
        """
        new: Add the new units/buildings to the current selection.
        """
        if selection_type == 'new':
            selection_game_ids = self.event['m_delta']['m_addUnitTags']
            self._add_to_selection(ctrl_group_num, selection_game_ids)

    def _handle_new_selection(self, ctrl_group_num):
        """
        ZeroIndices: Occurs on a new selection of units/buildings

        Example: A player has 10 Roaches originally selected, then
        selects 20 Zerglings.

        -----

        OneIndices: An alternative to Masks. A OneIndices selection occurs
        when a unit/building is deselected, when a unit/building in the
        original selection dies and when a unit/building in a control group
        dies.

        This event occurs in both the current selection (If the relevant
        units are selected) and any controls groups the units are apart of.

        Example: A player Shift-deselects a unit from their original selection.

        Note: The current selection is resolved immediately, but
        any control groups containing the units in the event
        are not resolved until they are reselected.

        -----

        Mask: A Mask subselection occurs when more than 1 unit/building
        is selected from the original selection.

        Example: A player has 18 Zerglings originally selected, then they
        box a subselection of 7 Zerglings.

        -----

        None: Occurs when units/buildings are added to the current selection.

        Example: A player has 18 Zerglings originally selected, then they
        box a new selection of 24 Zerglings, including the original 18.
        """
        event = self.event

        if 'ZeroIndices' in event['m_delta']['m_removeMask']:
            self._handle_zero_indices(ctrl_group_num, selection_type='new')

        elif 'OneIndices' in event['m_delta']['m_removeMask']:
            self._handle_one_indices(ctrl_group_num, selection_type='new')

        elif 'Mask' in event['m_delta']['m_removeMask']:
            self._handle_mask(ctrl_group_num, selection_type='new')

        elif 'None' in event['m_delta']['m_removeMask']:
            self._handle_none(ctrl_group_num, selection_type='new')

    def _handle_subselection(self, ctrl_group_num):
        """
        ZeroIndices: Occurs on a subselection when there is a
        maximum of 1 unit/building selected for every 8 in the
        original selection and the units/buildings are adjacent.

        Example: A player has 18 Zerglings originally selected,
        then they box a subselection of 2 Zerglings which are in
        positions 4 and 5 of the original selection.

        -----

        OneIndices: An alternative to Masks. A subselection OneIndices
        occurs when units need to be added to the selection as well as
        removed. This occurs when a Zerg unit is born from an Egg and
        when 2 units are morphed together to create a new unit.

        This event occurs in both the current selection (If the relevant
        units are selected) and any controls groups the units are apart of.

        Example: 2 High Templar are morphed into an Archon. Both
        High Templar are removed from the current selection and
        an Archon is inserted into the current selection.

        Note: The current selection is resolved immediately, but
        any control groups containing the units in the event
        are not resolved until they are reselected.

        -----

        Mask: A Mask subselection occurs when extra units/buildings are
        selected in addition to the original selection.

        Example: A player has 18 Zerglings originally selected, then they
        box a new selection of 24 Zerglings, including the original 18.
        """
        event = self.event

        if 'ZeroIndices' in event['m_delta']['m_removeMask']:
            self._handle_zero_indices(ctrl_group_num, selection_type='sub')

        elif 'OneIndices' in event['m_delta']['m_removeMask']:
            self._handle_one_indices(ctrl_group_num, selection_type='sub')

        elif 'Mask' in event['m_delta']['m_removeMask']:
            self._handle_mask(ctrl_group_num, selection_type='sub')

    def parse_event(self):
        player = self.player
        event = self.event
        ctrl_group_num = None

        if player:
            # if not default player selection
            if event['m_controlGroupId'] != 10:
                # ctrl_group_num = event['m_controlGroupId']
                # current_selection = self.player.control_groups[ctrl_group_num]

                # print(f'Control Group {ctrl_group_num},', round(event['_gameloop']/22.4/60.0, 1), 'min')
                # selection = {}
                # for obj in current_selection:
                #     if obj.name in selection:
                #         selection[obj.name] += 1
                #     else:
                #         selection[obj.name] = 1

                # for name, count in selection.items():
                #     print(name, count)
                # print(event)
                # print()
                return

            selection_game_ids = self.event['m_delta']['m_addUnitTags']
            for obj_game_id in selection_game_ids:
                if obj_game_id not in self.player.objects:
                    return

            if event['m_delta']['m_addSubgroups']:
                for unit in event['m_delta']['m_addSubgroups']:
                    if unit['m_unitLink'] == 125:
                        return
                self._handle_new_selection(ctrl_group_num)
            else:
                self._handle_subselection(ctrl_group_num)

            # if player.player_id == 1:
            #     if ctrl_group_num:
            #         current_selection = player.control_groups[ctrl_group_num]
            #     else:
            #         current_selection = player.current_selection
            #     print(player.name)
            #     print(f'Control Group {ctrl_group_num},', round(event['_gameloop']/22.4/60.0, 1), 'min')
            #     selection = {}
            #     for obj in current_selection:
            #         if obj.name in selection:
            #             selection[obj.name] += 1
            #         else:
            #             selection[obj.name] = 1

            #     for name, count in selection.items():
            #         print(name, count)
            #     print(event)
            #     print()


class ControlGroupEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def _set_obj_group_info(self, ctrl_group_num):
        ctrl_group = self.player.control_groups[ctrl_group_num]

        for index, obj in enumerate(ctrl_group):
            obj.control_groups[ctrl_group_num] = index

    def _remove_obj_group_info(self, ctrl_group_num):
        ctrl_group = self.player.control_groups[ctrl_group_num]

        for index, obj in enumerate(ctrl_group):
            for group_num, group_info in obj.control_groups.items():
                if index == group_num:
                    del obj.control_groups[index]
                    break

    def _copy_from_selection(self, target, selection):
        for obj in selection:
            if obj not in target:
                target.append(obj)

    def _add_to_group(self, ctrl_group_num):
        new_obj_list = self.player.current_selection
        control_group = self.player.control_groups[ctrl_group_num]

        for new_obj in new_obj_list:
            duplicate = False
            for old_obj in control_group:
                if new_obj.game_id == old_obj.game_id:
                    duplicate = True
                    break

            if not duplicate:
                control_group.append(new_obj)

        control_group.sort(key=lambda x: x.tag)

    def _create_bitmask(self, mask_x, mask_y, length):
        bitmask = bin(mask_y)[2:]

        ceil = math.ceil(len(bitmask)/8)
        if len(bitmask) % 8 != 0:
            bitmask = bitmask.rjust(ceil * 8, '0')

        bitmask_sects = []
        for i in range(0, ceil + 1):
            section = bitmask[8 * i:(8 * i) + 8]
            bitmask_sects.append(section[::-1])

        final_bitmask = ''.join(bitmask_sects)

        if len(final_bitmask) > length:
            final_bitmask = final_bitmask[:length + 1]
        else:
            final_bitmask = final_bitmask.ljust(length, '0')

        return final_bitmask

    def _remove_from_group(self, ctrl_group_num):
        """
        new:

        sub:
        """
        player = self.player
        event = self.event
        mask_x = event['m_mask']['Mask'][0]
        mask_y = event['m_mask']['Mask'][1]
        length = len(player.control_groups[ctrl_group_num])

        bitmask = self._create_bitmask(mask_x, mask_y, length)

        for i in range(length - 1, -1, -1):
            if bitmask[i] == '1':
                del player.control_groups[ctrl_group_num][i]

    def parse_event(self):
        """
        Each 'm_controlGroupUpdate' value corresponds to
        a different type of action.

        -----

        0: Bind the current selection to a control group.

        Example: A player uses Ctrl+1 to bind their
        current selection to control group 1.

        -----

        1: Add the current selection to a control group.

        Example: A player uses Shift+1 to add their
        current selection to control group 1.

        -----

        2: Select a control group.

        Example: A player presses 1 to select the units
        they bound to control group 1.

        -----

        3: Remove a control group.

        Example: A player presses 1, then Alt+3 to
        select the units they bound to control group 1
        and rebind them to control group 3. In this case
        control group 1 is removed.

        -----

        4: Overwrite a control group.

        Example: A player selects a unit already bound
        to control group 1, then presses Alt+3 to
        to rebind the unit to control group 3. In this case
        control group 1 is overwritten with a new version
        that does not include the unit that was removed.
        """
        player = self.player
        event = self.event
        ctrl_group_num = event['m_controlGroupIndex']

        # if player.player_id == 1:
        #     print(player.name)
        #     selection = {}
        #     for obj in player.current_selection:
        #         if obj.name in selection:
        #             selection[obj.name] += 1
        #         else:
        #             selection[obj.name] = 1

        #     for name, count in selection.items():
        #         print(name, count)

        if event['m_controlGroupUpdate'] == 0:
            player.control_groups[ctrl_group_num] = []
            control_group = player.control_groups[ctrl_group_num]
            self._copy_from_selection(control_group, player.current_selection)
            self._set_obj_group_info(ctrl_group_num)

        if event['m_controlGroupUpdate'] == 1:
            if ctrl_group_num not in player.control_groups:
                player.control_groups[ctrl_group_num] = []
            if 'Mask' in event['m_mask']:
                self._remove_from_group(ctrl_group_num)
            else:
                self._add_to_group(ctrl_group_num)
            self._set_obj_group_info(ctrl_group_num)

        if event['m_controlGroupUpdate'] == 2:
            player.current_selection = []
            control_group = player.control_groups[ctrl_group_num]
            self._copy_from_selection(player.current_selection, control_group)

        if event['m_controlGroupUpdate'] == 3:
            self._remove_obj_group_info(ctrl_group_num)
            del player.control_groups[ctrl_group_num]

        if event['m_controlGroupUpdate'] == 4:
            player.control_groups[ctrl_group_num] = []
            control_group = player.control_groups[ctrl_group_num]
            self._copy_from_selection(control_group, player.current_selection)
            self._set_obj_group_info(ctrl_group_num)

        # if player.player_id == 1:
        #     print(f'Control Group {ctrl_group_num},', round(event['_gameloop']/22.4/60.0, 1), 'min')
        #     selection = {}
        #     for obj in player.current_selection:
        #         if obj.name in selection:
        #             selection[obj.name] += 1
        #         else:
        #             selection[obj.name] = 1

        #     for name, count in selection.items():
        #         print(name, count)
        #     print(player.current_selection)
        #     print(event)
        #     print()


class UpgradeEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        pass


class CameraUpdateEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        if self.event['m_target']:
            player = self.player
            position = (self.event['m_target']['x'], self.event['m_target']['y'])
            gameloop = self.event['_gameloop']

            if self.player.current_pac:
                current_pac = self.player.current_pac
                # If current PAC is still within camera bounds, count action
                if current_pac.check_position(position):
                    current_pac.camera_moves.append((gameloop, position))

                # If current PAC is out of camera bounds
                # and meets min duration, save it
                elif current_pac.check_duration(gameloop):
                    current_pac.final_camera_position = position
                    current_pac.final_gameloop = gameloop

                    if current_pac.actions:
                        player.pac_list.append(current_pac)
                    player.current_pac = PerceptionActionCycle(position, gameloop)
                    player.current_pac.camera_moves.append((gameloop, position))

                # If current PAC is out of camera bounds
                # and does not meet min duration,
                # discard current PAC and create new one
                else:
                    player.current_pac = PerceptionActionCycle(position, gameloop)
                    player.current_pac.camera_moves.append((gameloop, position))
            else:
                player.current_pac = PerceptionActionCycle(position, gameloop)
                player.current_pac.camera_moves.append((gameloop, position))


class PlayerStatsEvent(BaseEvent):
    def __init__(self, summary_stats, *args):
        super().__init__(*args)
        self.summary_stats = summary_stats

    def parse_event(self):
        player = self.player
        gameloop = self.event['_gameloop']
        event = self.event
        summary_stats = self.summary_stats
        unspent_resources = self.player.unspent_resources
        collection_rate = self.player.collection_rate

        if gameloop != 1:
            unspent_resources['minerals'].append(
                event['m_stats']['m_scoreValueMineralsCurrent']
            )
            unspent_resources['gas'].append(
                event['m_stats']['m_scoreValueVespeneCurrent']
            )

            collection_rate['minerals'].append(
                event['m_stats']['m_scoreValueMineralsCollectionRate']
            )
            collection_rate['gas'].append(
                event['m_stats']['m_scoreValueVespeneCollectionRate']
            )

        if gameloop == self.game.game_length:
            summary_stats['resources_lost']['minerals'][player.player_id] = event['m_stats']['m_scoreValueMineralsLostArmy']
            summary_stats['resources_lost']['gas'][player.player_id] = event['m_stats']['m_scoreValueVespeneLostArmy']

            player_minerals = player.unspent_resources['minerals']
            player_gas = player.unspent_resources['gas']
            summary_stats['avg_unspent_resources']['minerals'][player.player_id] = round(
                sum(player_minerals)/len(player_minerals), 1
            )
            summary_stats['avg_unspent_resources']['gas'][player.player_id] = round(
                sum(player_gas)/len(player_gas), 1
            )

            player_minerals_collection = player.collection_rate['minerals']
            player_gas_collection = player.collection_rate['gas']
            summary_stats['avg_resource_collection_rate']['minerals'][player.player_id] = round(
                sum(player_minerals_collection)/len(player_minerals_collection), 1
            )
            summary_stats['avg_resource_collection_rate']['gas'][player.player_id] = round(
                sum(player_gas_collection)/len(player_gas_collection), 1
            )

            total_collection_rate = summary_stats['avg_resource_collection_rate']['minerals'][player.player_id] + summary_stats['avg_resource_collection_rate']['gas'][player.player_id]
            total_avg_unspent = summary_stats['avg_unspent_resources']['minerals'][player.player_id] + summary_stats['avg_unspent_resources']['gas'][player.player_id]
            player_sq = player.calc_sq(unspent_resources=total_avg_unspent, collection_rate=total_collection_rate)
            summary_stats['sq'][player.player_id] = player_sq

            current_workers = event['m_stats']['m_scoreValueWorkersActiveCount']
            workers_produced = summary_stats['workers_produced'][player.player_id]
            summary_stats['workers_lost'][player.player_id] = workers_produced + 12 - current_workers

        return summary_stats


class PlayerLeaveEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        pass
