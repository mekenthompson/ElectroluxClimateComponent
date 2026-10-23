"""Diagnostic sensors for values the climate entity does not show."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ElectroluxCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ElectroluxStatusCodeSensor(coordinator)])


class ElectroluxStatusCodeSensor(CoordinatorEntity[ElectroluxCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "status_code"
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator: ElectroluxCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}-status-code"
        self._attr_device_info = coordinator.device_info()

    @property
    def native_value(self) -> int | None:
        value = (self.coordinator.data or {}).get("ac_errcode")
        return value if isinstance(value, int) else None
