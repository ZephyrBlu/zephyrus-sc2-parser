class PerceptionActionCycle:
    def __init__(self, initial_camera_position, initial_gameloop):
        self.initial_camera_position = initial_camera_position
        self.initial_gameloop = initial_gameloop
        self.final_camera_position = None
        self.final_gameloop = None
        self.actions = []
        self.camera_moves = []
        self.min_duration = 4  # 4 game loops (~2sec) minimum
        self.min_camera_move = 6  # 6 camera units (x or y) minimum

    def check_position(self, new_position):
        """
        Compares the initial camera position of the PAC
        to the current camera position.

        If the current position differs by more than 6
        units, a boolean (False) is returned and the current PAC ends.
        """
        x_diff = abs(new_position.x - self.initial_camera_position.x)
        y_diff = abs(new_position.y - self.initial_camera_position.y)
        total_diff = (x_diff ** 2) + (y_diff ** 2)

        if total_diff > self.min_camera_move ** 2:
            return False
        return True

    def check_duration(self, new_gameloop):
        """
        Compares the initial gameloop the PAC
        started on to the current gameloop.

        If the difference is greater than 4 units,
        the PAC is valid and a boolean (True) is returned.
        """
        if new_gameloop - self.initial_gameloop > self.min_duration:
            return True
        return False
