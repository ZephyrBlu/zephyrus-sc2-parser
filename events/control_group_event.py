from zephyrus_sc2_parser.events.base_event import BaseEvent
import math


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
