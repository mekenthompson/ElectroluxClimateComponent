"""Unit off timer. This is the air conditioner's own sleep timer."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ElectroluxCoordinator
from .state import off_timer_minutes, split_timer_minutes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ElectroluxSleepTimerNumber(coordinator)])


class ElectroluxSleepTimerNumber(CoordinatorEntity[ElectroluxCoordinator], NumberEntity):
    """Minutes until the unit turns itself off. Zero clears the timer."""

    _attr_has_entity_name = True
    _attr_translation_key = "sleep_timer"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = 0
    _attr_native_max_value = 23 * 60 + 59
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: ElectroluxCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}-sleep-timer"
        self._attr_device_info = coordinator.device_info()

    @property
    def native_value(self) -> float:
        return float(off_timer_minutes(self.coordinator.data or {}))

    async def async_set_native_value(self, value: float) -> None:
        hours, minutes = split_timer_minutes(int(round(value)))
        await self.hass.async_add_executor_job(
            self.coordinator.device.set_timer,
            False,
            hours,
            minutes,
        )
        await self.coordinator.async_request_refresh()
