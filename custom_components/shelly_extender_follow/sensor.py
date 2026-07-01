"""Sensor exposing how the client Shelly is currently reachable."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    ATTR_CLIENT_MAC,
    ATTR_HOST,
    ATTR_IP,
    ATTR_LAST_RECONFIGURE,
    ATTR_MPORT,
    ATTR_PORT,
    ATTR_SSID,
    DOMAIN,
    VIA_DIRECT,
    VIA_EXTENDER,
    VIA_UNREACHABLE,
)
from .coordinator import ShellyExtenderFollowCoordinator
from .entity import ShellyExtenderFollowEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the reachability sensor."""
    coordinator: ShellyExtenderFollowCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ShellyLinkSensor(coordinator, entry)])


class ShellyLinkSensor(ShellyExtenderFollowEntity, SensorEntity):
    """Reports direct / extender / unreachable, with endpoint attributes."""

    _attr_translation_key = "link"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_options = [VIA_DIRECT, VIA_EXTENDER, VIA_UNREACHABLE]

    @property
    def unique_id(self) -> str:
        """Return a stable unique id derived from the config entry."""
        return f"{self._entry.entry_id}_link"

    @property
    def native_value(self) -> str | None:
        """Return the current reachability classification."""
        return self.coordinator.data.via if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Expose the resolved endpoint and diagnostics."""
        data = self.coordinator.data
        if data is None:
            return {}
        return {
            ATTR_HOST: data.host,
            ATTR_PORT: data.port,
            ATTR_SSID: data.ssid,
            ATTR_IP: data.ip,
            ATTR_MPORT: data.mport,
            ATTR_CLIENT_MAC: data.client_mac,
            ATTR_LAST_RECONFIGURE: data.last_reconfigure,
        }
