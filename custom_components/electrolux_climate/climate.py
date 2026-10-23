"""Climate entity for a Kelvinator / Electrolux Broadlink unit.

Written against Home Assistant 2026.10.2 ClimateEntity. That class still
reads current_temperature, target_temperature and temperature_unit. The
contributor docs' native_* names are not on this core.
"""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    PRESET_NONE,
    SWING_OFF,
    SWING_VERTICAL,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MAX, DEFAULT_MIN, DOMAIN, FAN_QUIET, FAN_TURBO
from .coordinator import ElectroluxCoordinator
from .electrolux import electrolux
from .state import (
    MARK_BY_FAN,
    PRESET_FREEZE,
    fan_mode,
    hvac_action,
    hvac_mode,
    mode_for_hvac,
    mode_for_preset,
    preset_mode,
    swing_vertical,
)

_HVAC = {item.value: item for item in HVACMode}
_ACTION = {item.value: item for item in HVACAction}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ElectroluxClimateEntity(coordinator)])


class ElectroluxClimateEntity(CoordinatorEntity[ElectroluxCoordinator], ClimateEntity):
    """One climate entity. The device name lives on the device, not the entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "unit"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = PRECISION_WHOLE
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_QUIET, FAN_TURBO]
    _attr_swing_modes = [SWING_OFF, SWING_VERTICAL]
    _attr_preset_modes = [PRESET_NONE, PRESET_FREEZE]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: ElectroluxCoordinator) -> None:
        super().__init__(coordinator)
        data = coordinator.config_entry.data
        self._attr_unique_id = coordinator.serial
        self._attr_device_info = coordinator.device_info()
        self._attr_min_temp = data.get(ATTR_MIN_TEMP, DEFAULT_MIN)
        self._attr_max_temp = data.get(ATTR_MAX_TEMP, DEFAULT_MAX)
        self._apply()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._apply()
        super()._handle_coordinator_update()

    def _apply(self) -> None:
        status = self.coordinator.data or {}
        if not status:
            return
        self._attr_hvac_mode = _HVAC[hvac_mode(status)]
        self._attr_hvac_action = _ACTION[hvac_action(status)]
        self._attr_preset_mode = preset_mode(status)
        self._attr_current_temperature = status.get("envtemp")
        self._attr_target_temperature = status.get("temp")
        self._attr_fan_mode = fan_mode(status)
        self._attr_swing_mode = swing_vertical(status)
        self._attr_device_info = self.coordinator.device_info()

    async def async_set_hvac_mode(self, hvac_mode_value: HVACMode) -> None:
        mode = hvac_mode_value.value if isinstance(hvac_mode_value, HVACMode) else str(hvac_mode_value)
        await self.hass.async_add_executor_job(self._set_hvac_mode, mode)
        await self.coordinator.async_request_refresh()

    def _set_hvac_mode(self, mode: str) -> None:
        device = self.coordinator.device
        if mode == HVACMode.OFF:
            device.set_power(False)
            return
        if not (self.coordinator.data or {}).get("ac_pwr"):
            device.set_power(True)
        device.set_mode(electrolux.mode(mode_for_hvac(mode)))

    async def async_set_preset_mode(self, preset: str) -> None:
        await self.hass.async_add_executor_job(self._set_preset_mode, preset)
        await self.coordinator.async_request_refresh()

    def _set_preset_mode(self, preset: str) -> None:
        device = self.coordinator.device
        protocol_mode = mode_for_preset(preset)
        if protocol_mode is None:
            if (self.coordinator.data or {}).get("ac_mode") == 6:
                device.set_mode(electrolux.mode(mode_for_hvac(HVACMode.HEAT)))
            return
        if not (self.coordinator.data or {}).get("ac_pwr"):
            device.set_power(True)
        device.set_mode(electrolux.mode(protocol_mode))

    async def async_set_fan_mode(self, fan_mode_value: str) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.device.set_fan,
            electrolux.fan(MARK_BY_FAN.get(fan_mode_value, 0)),
        )
        await self.coordinator.async_request_refresh()

    async def async_set_swing_mode(self, swing_mode_value: str) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.device.set_swing,
            swing_mode_value == SWING_VERTICAL,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs) -> None:
        if (mode := kwargs.get(ATTR_HVAC_MODE)) is not None:
            await self.async_set_hvac_mode(mode)
        if ATTR_TEMPERATURE not in kwargs:
            return
        target = int(round(float(kwargs[ATTR_TEMPERATURE])))
        await self.hass.async_add_executor_job(self.coordinator.device.set_temp, target)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_power, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_power, False)
        await self.coordinator.async_request_refresh()
