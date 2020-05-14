from .base_event import BaseEvent


class PlayerLeaveEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        pass
