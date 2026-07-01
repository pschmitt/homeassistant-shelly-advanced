"""Shared entity base for the Shelly Extender Follow integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ShellyExtenderFollowCoordinator


class ShellyExtenderFollowEntity(
    CoordinatorEntity[ShellyExtenderFollowCoordinator]
):
    """Base entity bound to the integration's single service device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ShellyExtenderFollowCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="pschmitt",
            entry_type=DeviceEntryType.SERVICE,
        )
