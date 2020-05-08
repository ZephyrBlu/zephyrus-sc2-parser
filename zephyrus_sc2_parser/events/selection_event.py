from zephyrus_sc2_parser.events.base_event import BaseEvent
import math


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

    def _is_morph(self):
        units = self.game.gamedata['units']

        # checking for Archon being added
        for obj_type in self.event['m_delta']['m_addSubgroups']:
            if obj_type['m_unitLink'] == units['Protoss']['Archon']['obj_id']:
                return True
        return False

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
            is_morph = self._is_morph()

            # reverse order of current selection so object removals
            # don't affect future removals
            for i in range(len(selection) - 1, -1, -1):
                if i in selection_indices:
                    if is_morph:
                        selection[i].morph_time = self.gameloop
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
            final_bitmask = final_bitmask[:length]
        else:
            final_bitmask = final_bitmask.ljust(length, '0')

        return final_bitmask

    def _handle_mask(self, ctrl_group_num, *, selection_type):
        """
        new:

        sub:
        """
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
                if selection_type == 'new' and self._is_morph():
                    selection[i].morph_time = self.gameloop
                del selection[i]

        if selection_type == 'new':
            self._add_to_selection(ctrl_group_num, event['m_delta']['m_addUnitTags'])

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
