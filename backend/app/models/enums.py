import enum


class LocationEnum(str, enum.Enum):
    READY_AREA = "READY_AREA"
    WRM_LINE = "WRM_LINE"
    WIP = "WIP"


class StatusEnum(str, enum.Enum):
    YET_TO_READY = "YET_TO_READY"
    PENDING = "PENDING"
    INP = "INP"
    GAUGING = "GAUGING"
    HYDROTEST = "HYDROTEST"
    READY = "READY"
    INSTALLED = "INSTALLED"


class EntryGuideConditionEnum(str, enum.Enum):
    NEW = "NEW"
    OLD = "OLD"
