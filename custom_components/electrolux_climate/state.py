"""Pure status mapping for Kelvinator / Electrolux Broadlink units.

No Home Assistant imports. The climate entity maps these strings onto the
2026.10 ClimateEntity enums.
"""

from __future__ import annotations

MODE_COOL = 0
MODE_HEAT = 1
MODE_DRY = 2
MODE_FAN = 3
MODE_AUTO = 4
MODE_HEAT_8 = 6

HVAC_OFF = "off"
HVAC_HEAT = "heat"
HVAC_COOL = "cool"
HVAC_AUTO = "auto"
HVAC_DRY = "dry"
HVAC_FAN_ONLY = "fan_only"

PRESET_NONE = "none"
PRESET_FREEZE = "freeze_protect"

ACTION_OFF = "off"
ACTION_COOLING = "cooling"
ACTION_HEATING = "heating"
ACTION_DRYING = "drying"
ACTION_FAN = "fan"
ACTION_IDLE = "idle"
ACTION_DEFROSTING = "defrosting"

FAN_BY_MARK = {
    0: "auto",
    1: "low",
    2: "medium",
    3: "high",
    4: "turbo",
    5: "quiet",
}
MARK_BY_FAN = {value: key for key, value in FAN_BY_MARK.items()}

HVAC_BY_MODE = {
    MODE_AUTO: HVAC_AUTO,
    MODE_COOL: HVAC_COOL,
    MODE_HEAT: HVAC_HEAT,
    MODE_DRY: HVAC_DRY,
    MODE_FAN: HVAC_FAN_ONLY,
}
MODE_BY_HVAC = {value: key for key, value in HVAC_BY_MODE.items()}

HVAC_MODES = (
    HVAC_OFF,
    HVAC_AUTO,
    HVAC_HEAT,
    HVAC_COOL,
    HVAC_DRY,
    HVAC_FAN_ONLY,
)


def _powered(status: dict) -> bool:
    return status.get("ac_pwr") == 1


def hvac_mode(status: dict) -> str:
    """Return the HVAC mode string. 8°C heat stays heat; the preset distinguishes it."""
    if not _powered(status):
        return HVAC_OFF
    mode = status.get("ac_mode")
    if mode == MODE_HEAT_8:
        return HVAC_HEAT
    return HVAC_BY_MODE.get(mode, HVAC_AUTO)


def preset_mode(status: dict) -> str:
    """Return the preset. Only 8°C heat is a preset; sleep is a separate switch."""
    if _powered(status) and status.get("ac_mode") == MODE_HEAT_8:
        return PRESET_FREEZE
    return PRESET_NONE


def hvac_action(status: dict) -> str:
    """Return what the unit is doing, from hardware bits, not from the mode alone."""
    if not _powered(status):
        return ACTION_OFF
    if status.get("ac_evapordefroststate"):
        return ACTION_DEFROSTING
    mode = status.get("ac_mode")
    heating = bool(status.get("ac_heaterstatus")) or (
        bool(status.get("ac_compressorstatus")) and mode in (MODE_HEAT, MODE_HEAT_8)
    )
    if heating:
        return ACTION_HEATING
    if status.get("ac_compressorstatus") and mode == MODE_DRY:
        return ACTION_DRYING
    if status.get("ac_compressorstatus"):
        return ACTION_COOLING
    if status.get("ac_indoorfanstatus"):
        return ACTION_FAN
    return ACTION_IDLE


def fan_mode(status: dict) -> str:
    mark = status.get("ac_mark")
    if not isinstance(mark, int):
        return "auto"
    return FAN_BY_MARK.get(mark, "auto")


def swing_vertical(status: dict) -> str:
    return "vertical" if status.get("ac_vdir") else "off"


def swing_horizontal(status: dict) -> str:
    return "on" if status.get("ac_hdir") else "off"


def off_timer_minutes(status: dict) -> int:
    """Minutes until the unit turns itself off. Second timer slot, proven live."""
    raw = status.get("timer")
    if not isinstance(raw, str):
        return 0
    parts = raw.split("|")
    if len(parts) < 3 or len(parts[2]) != 4 or not parts[2].isdigit():
        return 0
    hours = int(parts[2][:2])
    minutes = int(parts[2][2:])
    return hours * 60 + minutes


def split_timer_minutes(total: int) -> tuple[int, int]:
    total = max(0, min(int(total), 23 * 60 + 59))
    return divmod(total, 60)


def mode_for_hvac(hvac_mode_value: str) -> int:
    mode = MODE_BY_HVAC.get(hvac_mode_value)
    if mode is None:
        raise ValueError(f"unsupported hvac mode {hvac_mode_value}")
    return mode


def mode_for_preset(preset: str) -> int | None:
    if preset == PRESET_FREEZE:
        return MODE_HEAT_8
    if preset == PRESET_NONE:
        return None
    raise ValueError(f"unsupported preset {preset}")
