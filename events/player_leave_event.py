from zephyrus_sc2_parser.events.base_event import BaseEvent


class PlayerLeaveEvent(BaseEvent):
    def __init__(self, *args):
        super().__init__(*args)

    def parse_event(self):
        pass
