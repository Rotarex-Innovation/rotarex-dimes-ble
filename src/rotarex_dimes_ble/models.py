"""Settings of the ROTAREX DIMES app that change how the level is shown."""

from __future__ import annotations

from enum import StrEnum


class Region(StrEnum):
    """Unit region selected in the ROTAREX DIMES app."""

    EUROPE = "europe"
    OTHER = "other"


class TankType(StrEnum):
    """Tank type selected in the ROTAREX DIMES app."""

    CAMPING_CYLINDER = "camping_cylinder"
    CAMPING_SMART = "camping_smart"
    CAMPING_TANK = "camping_tank"
    CYLINDER = "cylinder"
    TANK = "tank"
