"""Read-only unit status that does not belong on the climate entity."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    async_add_entities(
        [
            _BitSensor(coordinator, "compressor", "ac_compressorstatus", BinarySensorDeviceClass.RUNNING),
            _BitSensor(coordinator, "defrost", "ac_evapordefroststate", None),
            _BitSensor(coordinator, "horizontal_swing", "ac_hdir", None),
        ]
    )


class _BitSensor(CoordinatorEntity[ElectroluxCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: ElectroluxCoordinator,
        key: str,
        field: str,
        device_class: BinarySensorDeviceClass | None,
    ) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_translation_key = key
        self._attr_unique_id = f"{coordinator.serial}-{key}"
        self._attr_device_info = coordinator.device_info()
        self._attr_device_class = device_class

    @property
    def is_on(self) -> bool | None:
        status = self.coordinator.data or {}
        if self._field not in status:
            return None
        return status.get(self._field) == 1
