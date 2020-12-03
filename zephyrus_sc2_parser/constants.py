from dataclasses import dataclass


@dataclass(frozen=True)
class ObjStatus:
    LIVE: str = 'LIVE'
    DIED: str = 'DIED'
    IN_PROGRESS: str = 'IN_PROGRESS'


@dataclass(frozen=True)
class ObjType:
    UNIT: str = 'UNIT'
    BUILDING: str = 'BUILDING'
    WORKER: str = 'WORKER'
    SUPPLY: str = 'SUPPLY'


obj_status = ObjStatus()
obj_type = ObjType()
