import logging
from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.game import PerceptionActionCycle
from zephyrus_sc2_parser.dataclasses import Position

logger = logging.getLogger(__name__)


class CameraEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        event = self.event
        player = self.player
        gameloop = self.gameloop

        logger.debug(f'Parsing {self.type} at {gameloop}')

        if not player or not self.event['m_target']:
            return
        position = Position(
            event['m_target']['x'] / 256,
            event['m_target']['y'] / 256,
        )

        if not player.prev_screen_position:
            player.prev_screen_position = position
        else:
            x_diff = player.prev_screen_position.x - position.x
            y_diff = player.prev_screen_position.y - position.y

            # if x^2 + y^2 > 15^2 then add screen
            # 15 tiles is cut off
            if (x_diff ** 2) + (y_diff ** 2) >= 225:
                player.screens.append(gameloop)
            player.prev_screen_position = position

        if player.current_pac:
            current_pac = player.current_pac
            # if current PAC is still within camera bounds, count action
            if current_pac.check_position(position):
                current_pac.camera_moves.append((gameloop, position))

            # if current PAC is out of camera bounds
            # and meets min duration, save it
            elif current_pac.check_duration(gameloop):
                current_pac.final_camera_position = position
                current_pac.final_gameloop = gameloop

                if current_pac.actions:
                    player.pac_list.append(current_pac)
                player.current_pac = PerceptionActionCycle(position, gameloop)
                player.current_pac.camera_moves.append((gameloop, position))

            # if current PAC is out of camera bounds
            # and does not meet min duration,
            # discard current PAC and create new one
            else:
                player.current_pac = PerceptionActionCycle(position, gameloop)
                player.current_pac.camera_moves.append((gameloop, position))
        else:
            player.current_pac = PerceptionActionCycle(position, gameloop)
            player.current_pac.camera_moves.append((gameloop, position))
