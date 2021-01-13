from typing import Optional, List, Tuple
from zephyrus_sc2_parser.dataclasses import Gameloop, Position


class PerceptionActionCycle:
    """
    Perception Action Cycles (PACs) track player actions
    and camera movement over a period of time and calculate
    multiple stats related to the recorded data
    """
    def __init__(self, initial_camera_position: Position, initial_gameloop: Gameloop):
        self.initial_camera_position: Position = initial_camera_position
        self.initial_gameloop: int = initial_gameloop
        self.final_camera_position: Optional[Position] = None
        self.final_gameloop: Optional[Gameloop] = None
        self.actions: List[int] = []
        self.camera_moves: List[Tuple[Gameloop, Position]] = []
        self.MIN_DURATION: int = 4  # 4 game loops (~2sec) minimum
        self.MIN_CAMERA_MOVE: int = 6  # 6 camera units (x or y) minimum

    def check_position(self, new_position: Position) -> bool:
        """
        Compares the initial camera position of the PAC
        to the current camera position.

        If the current position differs by more than 6
        units, a boolean (False) is returned and the current PAC ends.
        """
        x_diff = abs(new_position.x - self.initial_camera_position.x)
        y_diff = abs(new_position.y - self.initial_camera_position.y)
        total_diff = (x_diff ** 2) + (y_diff ** 2)

        if total_diff > self.MIN_CAMERA_MOVE ** 2:
            return False
        return True

    def check_duration(self, new_gameloop: Gameloop) -> bool:
        """
        Compares the initial gameloop the PAC
        started on to the current gameloop.

        If the difference is greater than 4 units,
        the PAC is valid and a boolean (True) is returned.
        """
        if new_gameloop - self.initial_gameloop > self.MIN_DURATION:
            return True
        return False
