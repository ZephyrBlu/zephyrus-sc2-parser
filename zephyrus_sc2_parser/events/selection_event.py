import math
import logging
from typing import Union, Literal, List
from zephyrus_sc2_parser.events.base_event import BaseEvent

logger = logging.getLogger(__name__)
SelectionType = Union[Literal['new'], Literal['sub']]


class SelectionEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def _add_to_selection(self, ctrl_group_num: int, new_obj_ids: List[int]):
        player = self.player

        logger.debug('Adding new objects to current selection or control group')
        if ctrl_group_num:
            selection = player.control_groups[ctrl_group_num]
        else:
            selection = player.current_selection

        for obj_game_id in new_obj_ids:
            if obj_game_id not in player.objects:
                logger.warning(f'{obj_game_id} not in player objects. Returning')
                return

        for obj_game_id in new_obj_ids:
            obj = player.objects[obj_game_id]
            selection.append(obj)
            logger.debug(f'Added {obj} to control group {ctrl_group_num}')
        selection.sort(key=lambda x: x.tag)

        # update object control group references
        if ctrl_group_num:
            logger.debug('Updating object control group references')
            for index, obj in enumerate(selection):
                logger.debug(f'Object: {obj}')
                if ctrl_group_num not in obj.control_groups:
                    logger.debug(f'Previous reference: Does not exist')
                else:
                    logger.debug(f'Previous reference: control group {ctrl_group_num}, index {obj.control_groups[ctrl_group_num]}')
                obj.control_groups[ctrl_group_num] = index
                logger.debug(f'Updated reference: control group {ctrl_group_num}, index {obj.control_groups[ctrl_group_num]}')

        # re-assign selection to update object
        if ctrl_group_num:
            player.control_groups[ctrl_group_num] = selection
        else:
            player.current_selection = selection

    def _is_morph(self) -> bool:
        units = self.game.gamedata.units

        # checking for Archon being added
        for obj_type in self.event['m_delta']['m_addSubgroups']:
            if obj_type['m_unitLink'] == units['Protoss']['Archon']['obj_id']:
                return True
        return False

    def _handle_zero_indices(self, ctrl_group_num: int, *, selection_type: SelectionType):
        """
        new: Clear the current selection and create a new one
        containing the newly selected units/buildings

        sub: Sub-select the units/buildings in the positions
        given by 'm_removeMask' from the current selection
        """
        player = self.player
        event = self.event

        logger.debug(f'Handling ZeroIndices mask on control group {ctrl_group_num} with {selection_type} selection')

        # new selection
        if selection_type == 'new':
            if ctrl_group_num:
                logger.debug(f'Clearing control group {ctrl_group_num}')
                player.control_groups[ctrl_group_num] = []
                selection = player.control_groups[ctrl_group_num]
            else:
                logger.debug('Clearing current selection')
                player.current_selection = []
                selection = player.current_selection

            new_game_ids = event['m_delta']['m_addUnitTags']

            for obj_game_id in new_game_ids:
                if obj_game_id in player.objects:
                    selection.append(player.objects[obj_game_id])
            selection.sort(key=lambda x: x.tag)

        # sub selection. i.e a subset of the existing selection
        elif selection_type == 'sub':
            if ctrl_group_num:
                selection = player.control_groups[ctrl_group_num]
            else:
                selection = player.current_selection

            selection_indices = event['m_delta']['m_removeMask']['ZeroIndices']
            logger.debug(f'Selection indices: {selection_indices}')

            for i in range(len(selection) - 1, -1, -1):
                if i not in selection_indices:
                    logger.debug(f'Removing object {selection[i]} at position {i}')
                    del selection[i]

        # re-assign selection to update object
        if ctrl_group_num:
            player.control_groups[ctrl_group_num] = selection
        else:
            player.current_selection = selection

    def _handle_one_indices(self, ctrl_group_num: int, *, selection_type: SelectionType):
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

        logger.debug(f'Handling OneIndices mask on control group {ctrl_group_num} with {selection_type} selection')
        logger.debug(f'Selection indices {selection_indices}')

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
                    logger.debug(f'Removing object {selection[i]} at position {i}')
                    del selection[i]

            # re-assign selection to update object
            if ctrl_group_num:
                player.control_groups[ctrl_group_num] = selection
            else:
                player.current_selection = selection

            self._add_to_selection(ctrl_group_num, new_game_ids)

        elif selection_type == 'sub':
            # reverse order of current selection so object removals
            # don't affect future removals
            for i in range(len(selection) - 1, -1, -1):
                if i in selection_indices:
                    logger.debug(f'Removing object {selection[i]} at position {i}')
                    del selection[i]

            # re-assign selection to update object
            if ctrl_group_num:
                player.control_groups[ctrl_group_num] = selection
            else:
                player.current_selection = selection

    def _create_bitmask(self, mask_x: int, mask_y: int, length: int):
        logger.debug('Creating bitmask')
        # remove 0b prefix from string
        bitmask = bin(mask_y)[2:]

        # ceil = number of bytes
        ceil = math.ceil(len(bitmask) / 8)
        # if we have more than 8 bits, we need to pad the string
        # to the correct number of bytes for the next operations
        if len(bitmask) % 8 != 0:
            bitmask_bytes = bitmask[:(ceil * 8) - 8]
            remaining_bits = bitmask[(ceil * 8) - 8:]
            bitmask = bitmask_bytes + remaining_bits.rjust(8, '0')

        # slice the bitmask into bytes, reverse the byte string and record it in order
        bitmask_sects = []
        for i in range(0, ceil):
            section = bitmask[8 * i:(8 * i) + 8]
            bitmask_sects.append(section[::-1])
        final_bitmask = ''.join(bitmask_sects)

        # adjust the created bitmask to the correct number of bits
        if len(final_bitmask) > length:
            final_bitmask = final_bitmask[:length]
        else:
            final_bitmask = final_bitmask.ljust(length, '0')
        logger.debug(f'Final bitmask: {final_bitmask}')
        return final_bitmask

    def _handle_mask(self, ctrl_group_num: int, *, selection_type: SelectionType):
        """
        new:

        sub:
        """
        player = self.player
        event = self.event
        mask_x = event['m_delta']['m_removeMask']['Mask'][0]
        mask_y = event['m_delta']['m_removeMask']['Mask'][1]

        logger.debug(f'Handling Mask on control group {ctrl_group_num} with {selection_type} selection')
        logger.debug(f'Mask: {mask_x}, {mask_y}')

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
                logger.debug(f'Removing object {selection[i]} at position {i}')
                del selection[i]

        # re-assign selection to update object
        if ctrl_group_num:
            player.control_groups[ctrl_group_num] = selection
        else:
            player.current_selection = selection

        if selection_type == 'new':
            self._add_to_selection(ctrl_group_num, event['m_delta']['m_addUnitTags'])

    def _handle_none(self, ctrl_group_num: int, *, selection_type: SelectionType):
        """
        new: Add the new units/buildings to the current selection.
        """
        logger.debug(f'Handling None on control group {ctrl_group_num} with {selection_type} selection')

        if selection_type == 'new':
            selection_game_ids = self.event['m_delta']['m_addUnitTags']
            self._add_to_selection(ctrl_group_num, selection_game_ids)

    def _handle_new_selection(self, ctrl_group_num: int):
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

        Mask: A Mask sub selection occurs when more than 1 unit/building
        is selected from the original selection.

        Example: A player has 18 Zerglings originally selected, then they
        box a sub selection of 7 Zerglings.

        -----

        None: Occurs when units/buildings are added to the current selection.

        Example: A player has 18 Zerglings originally selected, then they
        box a new selection of 24 Zerglings, including the original 18.
        """
        event = self.event

        logger.debug(f'Handling new selection on control group {ctrl_group_num}')

        if 'ZeroIndices' in event['m_delta']['m_removeMask']:
            self._handle_zero_indices(ctrl_group_num, selection_type='new')

        elif 'OneIndices' in event['m_delta']['m_removeMask']:
            self._handle_one_indices(ctrl_group_num, selection_type='new')

        elif 'Mask' in event['m_delta']['m_removeMask']:
            self._handle_mask(ctrl_group_num, selection_type='new')

        elif 'None' in event['m_delta']['m_removeMask']:
            self._handle_none(ctrl_group_num, selection_type='new')

    def _handle_sub_selection(self, ctrl_group_num: int):
        """
        ZeroIndices: Occurs on a sub selection when there is a
        maximum of 1 unit/building selected for every 8 in the
        original selection and the units/buildings are adjacent.

        Example: A player has 18 Zerglings originally selected,
        then they box a sub selection of 2 Zerglings which are in
        positions 4 and 5 of the original selection.

        -----

        OneIndices: An alternative to Masks. A sub selection OneIndices
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

        Mask: A Mask sub selection occurs when extra units/buildings are
        selected in addition to the original selection.

        Example: A player has 18 Zerglings originally selected, then they
        box a new selection of 24 Zerglings, including the original 18.
        """
        event = self.event

        logger.debug(f'Handling sub selection on control group {ctrl_group_num}')

        if 'ZeroIndices' in event['m_delta']['m_removeMask']:
            self._handle_zero_indices(ctrl_group_num, selection_type='sub')

        elif 'OneIndices' in event['m_delta']['m_removeMask']:
            self._handle_one_indices(ctrl_group_num, selection_type='sub')

        elif 'Mask' in event['m_delta']['m_removeMask']:
            self._handle_mask(ctrl_group_num, selection_type='sub')

    def parse_event(self):
        event = self.event
        player = self.player
        gameloop = self.gameloop

        # this event only concerns the player's current selection
        ctrl_group_num = None

        logger.debug(f'Parsing {self.type} at {gameloop}')
        logger.debug(f'Control group num: {ctrl_group_num}')
        logger.debug(f'm_controlGroupId: {event["m_controlGroupId"]}')

        if not player:
            logger.debug('No player associated with this event')
            return

        logger.debug(f'Player: {player.name} ({player.player_id})')

        # need to handle Egg hatching here
        if event['m_controlGroupId'] != 10:
            ctrl_group_num = event['m_controlGroupId']
            logger.debug(f'Control group (Before): {player.control_groups[ctrl_group_num]}')
            logger.debug(f'Current selection (Before): {player.current_selection}')

            # new selection handles adding units
            self._handle_new_selection(ctrl_group_num)

            logger.debug(f'Control group (After): {player.control_groups[ctrl_group_num]}')
            logger.debug(f'Current selection (After): {player.current_selection}')
            return

        selection_game_ids = self.event['m_delta']['m_addUnitTags']
        for obj_game_id in selection_game_ids:
            if obj_game_id not in self.player.objects:
                logger.debug(f'Object with game id {obj_game_id} not found in player objects')
                return

        logger.debug(f'Current selection (Before): {player.current_selection}')

        if event['m_delta']['m_addSubgroups']:
            for unit in event['m_delta']['m_addSubgroups']:
                # Egg. The morph from Larva -> Egg is handled on an object level
                # don't need to respond to this event
                if unit['m_unitLink'] == 125:
                    return
            self._handle_new_selection(ctrl_group_num)
        else:
            self._handle_sub_selection(ctrl_group_num)

        logger.debug(f'Current selection (After): {player.current_selection}')
