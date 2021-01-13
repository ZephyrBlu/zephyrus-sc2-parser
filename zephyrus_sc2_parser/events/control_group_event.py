import math
import logging
from typing import List
from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.game import GameObj

logger = logging.getLogger(__name__)


class ControlGroupEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def _set_obj_group_info(self, ctrl_group_num: int):
        logger.debug(f'Binding control group {ctrl_group_num} to objects')
        ctrl_group = self.player.control_groups[ctrl_group_num]

        for index, obj in enumerate(ctrl_group):
            obj.control_groups[ctrl_group_num] = index
            logger.debug(f'Binding control group {ctrl_group_num} to {obj} at position {index}')

    def _remove_obj_group_info(self, ctrl_group_num: int):
        logger.debug(f'Removing control group {ctrl_group_num} from objects')
        ctrl_group = self.player.control_groups[ctrl_group_num]

        for index, obj in enumerate(ctrl_group):
            for group_num, group_info in obj.control_groups.items():
                if ctrl_group_num == group_num and index == group_info:
                    del obj.control_groups[group_num]
                    logger.debug(f'Removed control group {ctrl_group_num} from {obj} at position {index}')
                    break

    def _copy_from_selection(self, selection: List[GameObj], target: List[GameObj]):
        logger.debug('Copying from selection to target')
        for obj in selection:
            if obj not in target:
                target.append(obj)

    def _add_to_group(self, ctrl_group_num: int):
        logger.debug(f'Adding current selection to control group {ctrl_group_num}')
        new_obj_list = self.player.current_selection
        control_group = self.player.control_groups[ctrl_group_num]

        # change control groups/selections to sets instead of lists?
        for new_obj in new_obj_list:
            duplicate = False
            for old_obj in control_group:
                if new_obj.game_id == old_obj.game_id:
                    duplicate = True
                    break

            if not duplicate:
                control_group.append(new_obj)
        control_group.sort(key=lambda x: x.tag)

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

    def _remove_from_group(self, ctrl_group_num: int):
        """
        new:

        sub:
        """
        player = self.player
        event = self.event
        # rename x, y. confusing
        mask_x = event['m_mask']['Mask'][0]
        mask_y = event['m_mask']['Mask'][1]
        length = len(player.control_groups[ctrl_group_num])

        logger.debug(f'Removing mask selection from control group {ctrl_group_num}')
        logger.debug(f'Mask: {mask_x}, {mask_y}')

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

        4: Steal and bind the current selection to a control group.

        Example: A player selects a unit already bound
        to control group 1, then presses Alt+3 to
        to rebind the unit to control group 3. In this case,
        the unit is removed from control group 1 and
        control group 3 is overwritten with the new control group
        that includes the unit that was removed.

        -----

        5: Steal and add the current selection to a control group.

        Example: A player selects a unit already bound
        to control group 1, then presses Shift+Alt+3 to
        to rebind the unit to control group 3. In this case,
        the unit is removed from control group 1 and added
        to control group 3.
        """
        player = self.player
        event = self.event
        ctrl_group_num = event['m_controlGroupIndex']

        logger.debug(f'Parsing {self.type} at {self.gameloop}')
        logger.debug(f'Player: {player.name} ({player.player_id})')
        logger.debug(f'Control group num: {ctrl_group_num}')

        if ctrl_group_num in player.control_groups:
            logger.debug(f'Control group (Before): {player.control_groups[ctrl_group_num]}')
        else:
            logger.debug(f'Control group (Before): Does not exist')
        logger.debug(f'Current selection (Before): {player.current_selection}')

        if event['m_controlGroupUpdate'] == 0:
            logger.debug('m_controlGroupUpdate = 0 (Binding current selection to control group)')
            player.control_groups[ctrl_group_num] = []
            control_group = player.control_groups[ctrl_group_num]
            self._copy_from_selection(player.current_selection, control_group)
            self._set_obj_group_info(ctrl_group_num)

        elif event['m_controlGroupUpdate'] == 1:
            logger.debug('m_controlGroupUpdate = 1 (Adding current selection to control group)')
            if ctrl_group_num not in player.control_groups:
                player.control_groups[ctrl_group_num] = []

            self._add_to_group(ctrl_group_num)
            # limited to Eggs hatches/Larva swapping?
            if 'Mask' in event['m_mask']:
                self._remove_from_group(ctrl_group_num)
            self._set_obj_group_info(ctrl_group_num)

        elif event['m_controlGroupUpdate'] == 2:
            logger.debug('m_controlGroupUpdate = 2 (Selecting control group)')
            player.current_selection = []

            if ctrl_group_num in player.control_groups:
                control_group = player.control_groups[ctrl_group_num]
            else:
                control_group = []
            self._copy_from_selection(control_group, player.current_selection)

        elif event['m_controlGroupUpdate'] == 3:
            logger.debug('m_controlGroupUpdate = 3 (Removing control group)')
            if ctrl_group_num in player.control_groups:
                self._remove_obj_group_info(ctrl_group_num)
                del player.control_groups[ctrl_group_num]

        elif event['m_controlGroupUpdate'] == 4:
            logger.debug('m_controlGroupUpdate = 4 (Steal and bind current selection to control group)')

            # control group may not exist yet
            if ctrl_group_num in player.control_groups:
                # remove references to control group from existing objects
                self._remove_obj_group_info(ctrl_group_num)

            # clear control group since we are overwriting
            player.control_groups[ctrl_group_num] = []
            control_group = player.control_groups[ctrl_group_num]

            # remove references to other control groups from objects to be added
            # this is control group 'stealing'
            logger.debug(f'Removing references to other control groups from objects')
            for obj in player.current_selection:
                obj.control_groups = {}

            # add new objects to control group
            self._copy_from_selection(player.current_selection, control_group)

            # set references to control group for new objects
            self._set_obj_group_info(ctrl_group_num)

        elif event['m_controlGroupUpdate'] == 5:
            logger.debug('m_controlGroupUpdate = 5 (Steal and add current selection to control group)')

            # remove references to other control groups from objects to be added
            # this is control group 'stealing'
            logger.debug(f'Removing references to other control groups from objects')
            for obj in player.current_selection:
                obj.control_groups = {}

            # this control group event can be called on an non-existent group
            if ctrl_group_num not in player.control_groups:
                player.control_groups[ctrl_group_num] = []

            # add new objects to control group
            self._add_to_group(ctrl_group_num)

            # set references to control group for new objects
            self._set_obj_group_info(ctrl_group_num)

        if ctrl_group_num in player.control_groups:
            logger.debug(f'Control group (After): {player.control_groups[ctrl_group_num]}')
        else:
            logger.debug(f'Control group (After): Does not exist')
        logger.debug(f'Current selection (After): {player.current_selection}')
