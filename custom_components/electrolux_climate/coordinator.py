"""Shared polling for one Kelvinator unit."""

from __future__ import annotations

import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .electrolux import electrolux

_LOGGER = logging.getLogger(__name__)


class ElectroluxCoordinator(DataUpdateCoordinator[dict]):
    """Poll one unit and share the status with climate and switch entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: electrolux,
        mac: bytes,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.device = device
        self.mac = mac
        self.model: str | None = None

    async def _async_update_data(self) -> dict:
        try:
            raw = await self.hass.async_add_executor_job(self.device.get_status)
            status = json.loads(raw)
        except (OSError, TimeoutError, json.JSONDecodeError) as err:
            raise UpdateFailed("status read failed") from err
        except Exception as err:
            # Broadlink raises its own exception types. Do not log the payload;
            # it contains the serial number.
            raise UpdateFailed("status read failed") from err
        model = status.get("modelnumber")
        if isinstance(model, str) and model:
            self.model = model
        return status

    @property
    def serial(self) -> str:
        status = self.data or {}
        serial = status.get("sn")
        if isinstance(serial, str) and serial:
            return serial
        return self.mac.hex()

    def device_info(self) -> dr.DeviceInfo:
        status = self.data or {}
        model = status.get("modelnumber") if isinstance(status.get("modelnumber"), str) else self.model
        return dr.DeviceInfo(
            connections={(dr.CONNECTION_NETWORK_MAC, dr.format_mac(self.mac.hex()))},
            identifiers={(DOMAIN, self.serial)},
            manufacturer="Kelvinator",
            model=model or None,
            name=self.config_entry.title,
        )
