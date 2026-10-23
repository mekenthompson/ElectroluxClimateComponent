"""Display and sleep switches for a Kelvinator unit."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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
            ElectroluxDisplaySwitch(coordinator),
            ElectroluxSleepSwitch(coordinator),
            ElectroluxSelfCleanSwitch(coordinator),
        ]
    )


class _ElectroluxSwitch(CoordinatorEntity[ElectroluxCoordinator], SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: ElectroluxCoordinator, suffix: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}-{suffix}"
        self._attr_device_info = coordinator.device_info()

    @property
    def _status(self) -> dict:
        return self.coordinator.data or {}


class ElectroluxDisplaySwitch(_ElectroluxSwitch):
    _attr_translation_key = "display"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:led-on"

    def __init__(self, coordinator: ElectroluxCoordinator) -> None:
        super().__init__(coordinator, "led")

    @property
    def is_on(self) -> bool | None:
        if "scrdisp" not in self._status:
            return None
        return self._status.get("scrdisp") == 1

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_led, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_led, False)
        await self.coordinator.async_request_refresh()


class ElectroluxSleepSwitch(_ElectroluxSwitch):
    _attr_translation_key = "sleep"
    _attr_icon = "mdi:sleep"

    def __init__(self, coordinator: ElectroluxCoordinator) -> None:
        super().__init__(coordinator, "sleep")

    @property
    def is_on(self) -> bool | None:
        if "ac_slp" not in self._status:
            return None
        return self._status.get("ac_slp") == 1

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_sleep, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_sleep, False)
        await self.coordinator.async_request_refresh()


class ElectroluxSelfCleanSwitch(_ElectroluxSwitch):
    """Unit self-clean. Reads mldprf and writes the existing set_self_clean command."""

    _attr_translation_key = "self_clean"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:broom"

    def __init__(self, coordinator: ElectroluxCoordinator) -> None:
        super().__init__(coordinator, "clean")

    @property
    def is_on(self) -> bool | None:
        if "mldprf" not in self._status:
            return None
        return self._status.get("mldprf") == 1

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_self_clean, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self.coordinator.device.set_self_clean, False)
        await self.coordinator.async_request_refresh()
