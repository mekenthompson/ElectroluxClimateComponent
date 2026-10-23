"""Mapping tests. No Home Assistant import."""

import importlib.util
from pathlib import Path
import unittest

_STATE = Path(__file__).resolve().parents[1] / "custom_components" / "electrolux_climate" / "state.py"
_spec = importlib.util.spec_from_file_location("electrolux_state", _STATE)
assert _spec and _spec.loader
_state = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_state)

HVAC_MODES = _state.HVAC_MODES
hvac_action = _state.hvac_action
hvac_mode = _state.hvac_mode
mode_for_hvac = _state.mode_for_hvac
preset_mode = _state.preset_mode


OFFICE = {
    "ac_pwr": 1,
    "ac_mode": 0,
    "ac_mark": 3,
    "ac_vdir": 0,
    "ac_compressorstatus": 1,
    "ac_heaterstatus": 0,
    "ac_indoorfanstatus": 1,
    "ac_evapordefroststate": 0,
    "envtemp": 31,
    "temp": 18,
}


class StateMapTest(unittest.TestCase):
    def test_live_cool_reports_cooling_not_heat_cool(self) -> None:
        self.assertEqual(hvac_mode(OFFICE), "cool")
        self.assertEqual(hvac_action(OFFICE), "cooling")
        self.assertEqual(preset_mode(OFFICE), "none")
        self.assertNotIn("heat_cool", HVAC_MODES)

    def test_eight_degree_heat_is_a_preset(self) -> None:
        status = {**OFFICE, "ac_mode": 6, "ac_compressorstatus": 0, "ac_heaterstatus": 1}
        self.assertEqual(hvac_mode(status), "heat")
        self.assertEqual(preset_mode(status), "freeze_protect")
        self.assertEqual(hvac_action(status), "heating")
        with self.assertRaises(ValueError):
            mode_for_hvac("heat_cool")

    def test_idle_when_compressor_and_fan_are_off(self) -> None:
        status = {
            **OFFICE,
            "ac_compressorstatus": 0,
            "ac_indoorfanstatus": 0,
            "ac_heaterstatus": 0,
        }
        self.assertEqual(hvac_action(status), "idle")

    def test_fan_when_only_the_fan_is_running(self) -> None:
        status = {
            **OFFICE,
            "ac_compressorstatus": 0,
            "ac_heaterstatus": 0,
            "ac_indoorfanstatus": 1,
        }
        self.assertEqual(hvac_action(status), "fan")

    def test_off_ignores_a_stale_mode(self) -> None:
        status = {**OFFICE, "ac_pwr": 0, "ac_mode": 6, "ac_compressorstatus": 1}
        self.assertEqual(hvac_mode(status), "off")
        self.assertEqual(hvac_action(status), "off")
        self.assertEqual(preset_mode(status), "none")

    def test_defrost_wins_over_compressor(self) -> None:
        status = {**OFFICE, "ac_evapordefroststate": 1}
        self.assertEqual(hvac_action(status), "defrosting")

    def test_integer_setpoint_round_trip_mode(self) -> None:
        self.assertEqual(mode_for_hvac("cool"), 0)
        self.assertEqual(mode_for_hvac("fan_only"), 3)


if __name__ == "__main__":
    unittest.main()
