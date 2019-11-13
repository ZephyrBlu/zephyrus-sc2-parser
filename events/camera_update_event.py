from .base_event import BaseEvent
from ..game.perception_action_cycle import PerceptionActionCycle


class CameraUpdateEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        if self.event['m_target']:
            player = self.player
            position = (self.event['m_target']['x'], self.event['m_target']['y'])
            gameloop = self.event['_gameloop']

            if not player:
                return

            elif self.player.current_pac:
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
