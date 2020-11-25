import math
import logging
from zephyrus_sc2_parser.events.base_event import BaseEvent

logger = logging.getLogger(__name__)


class ControlGroupEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def _set_obj_group_info(self, ctrl_group_num):
        logger.debug(f'Binding control group {ctrl_group_num} to objects')
        ctrl_group = self.player.control_groups[ctrl_group_num]

        for index, obj in enumerate(ctrl_group):
            obj.control_groups[ctrl_group_num] = index
            logger.debug(f'Binding control group {ctrl_group_num} to {obj} at position {index}')

    def _remove_obj_group_info(self, ctrl_group_num):
        logger.debug(f'Removing control group {ctrl_group_num} from objects')
        ctrl_group = self.player.control_groups[ctrl_group_num]

        for index, obj in enumerate(ctrl_group):
            for group_num, group_info in obj.control_groups.items():
                if ctrl_group_num == group_num and index == group_info:
                    del obj.control_groups[group_num]
                    logger.debug(f'Removed control group {ctrl_group_num} from {obj} at position {index}')
                    break

    def _copy_from_selection(self, selection, target):
        logger.debug('Copying from selection to target')
        logger.debug(f'Length before copying: selection {len(selection)}, target {len(target)}')
        for obj in selection:
            if obj not in target:
                target.append(obj)
        logger.debug(f'Length after copying: selection {len(selection)}, target {len(target)}')

    def _add_to_group(self, ctrl_group_num):
        logger.debug(f'Adding current selection to control group {ctrl_group_num}')
        new_obj_list = self.player.current_selection
        control_group = self.player.control_groups[ctrl_group_num]
        logger.debug(f'Control group length before adding current selection: {len(control_group)}')

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
        logger.debug(f'Control group length after adding current selection: {len(control_group)}')

    def _create_bitmask(self, mask_x, mask_y, length):
        logger.debug('Creating bitmask')
        # remove 0b prefix from string
        bitmask = bin(mask_y)[2:]

        # ceil = number of bytes
        ceil = math.ceil(len(bitmask)/8)
        # if we have more than 8 bits, we need to pad the string
        # to the correct number of bytes for the next operations
        if len(bitmask) % 8 != 0:
            bitmask = bitmask.rjust(ceil * 8, '0')

        # slice the bitmask into bytes, reverse the byte string and record it in order
        bitmask_sects = []
        for i in range(0, ceil + 1):
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

    def _remove_from_group(self, ctrl_group_num):
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

        logger.debug(f'Control group length before removal: {len(player.control_groups[ctrl_group_num])}')

        for i in range(length - 1, -1, -1):
            if bitmask[i] == '1':
                del player.control_groups[ctrl_group_num][i]
        logger.debug(f'Control group length after removal: {len(player.control_groups[ctrl_group_num])}')

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

        logger.debug(f'Parsing {self.event_type} at {self.gameloop}')
        logger.debug(f'Player: {player.name} ({player.player_id})')
        logger.debug(f'Control group num: {ctrl_group_num}')
        logger.debug(f'Control group (Before): {player.control_groups[ctrl_group_num]}')
        logger.debug(f'Current selection (Before): {player.current_selection}')

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
            logger.debug('m_controlGroupUpdate = 0 (Binding current selection to control group)')
            player.control_groups[ctrl_group_num] = []
            control_group = player.control_groups[ctrl_group_num]
            self._copy_from_selection(player.current_selection, control_group)
            self._set_obj_group_info(ctrl_group_num)

        elif event['m_controlGroupUpdate'] == 1:
            logger.debug('m_controlGroupUpdate = 1 (Adding current selection to control group)')
            if ctrl_group_num not in player.control_groups:
                player.control_groups[ctrl_group_num] = []

            if 'Mask' in event['m_mask']:
                self._remove_from_group(ctrl_group_num)
            else:
                self._add_to_group(ctrl_group_num)
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
            logger.debug('m_controlGroupUpdate = 4 (Overwriting control group)')
            player.control_groups[ctrl_group_num] = []
            control_group = player.control_groups[ctrl_group_num]
            self._copy_from_selection(player.current_selection, control_group)
            self._set_obj_group_info(ctrl_group_num)

        logger.debug(f'Control group (After): {player.control_groups[ctrl_group_num]}')
        logger.debug(f'Current selection (After): {player.current_selection}')

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
