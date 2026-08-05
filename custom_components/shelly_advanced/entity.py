"""Shared entity base for the Shelly Advanced integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_CLIENT_ENTRY_ID, DOMAIN
from .coordinator import ShellyAdvancedCoordinator


def _resolve_client_device(
    hass: HomeAssistant, entry: ConfigEntry, client_mac: str
) -> tuple[str | None, dr.DeviceEntry | None, DeviceInfo | None]:
    """Return (device_name, existing_device, fallback_device_info).

    Exactly one of existing_device/fallback_device_info is set. We attach to
    the existing Shelly device via entity.device_entry directly (rather than
    copying its identifiers/connections into DeviceInfo) so our entities
    appear on its page without creating a second device for the same
    physical Shelly. A device now belongs to a single config entry and no
    longer merges across integrations that share identifiers/connections
    (HA Core 2026.8, "single config entry per device"). The name is used to
    build clean entity_ids (see the base entity) that match the Shelly's own
    convention.
    """
    client_entry_id = entry.data[CONF_CLIENT_ENTRY_ID]
    dev_reg = dr.async_get(hass)
    device = next(
        (
            d
            for d in dev_reg.devices.values()
            if client_entry_id in d.config_entries and (d.identifiers or d.connections)
        ),
        None,
    )
    if device is None and client_mac:
        device = dev_reg.async_get_device(
            connections={(dr.CONNECTION_NETWORK_MAC, dr.format_mac(client_mac))}
        )
    if device is not None:
        return device.name_by_user or device.name, device, None
    return (
        entry.title,
        None,
        DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="pschmitt",
            entry_type=DeviceEntryType.SERVICE,
        ),
    )


class ShellyAdvancedEntity(CoordinatorEntity[ShellyAdvancedCoordinator]):
    """Base entity attached to the client Shelly's device."""

    _attr_has_entity_name = True
    # Subclasses set these so we can build a clean entity_id ourselves
    # (<platform>.<device>_<key>), avoiding HA's area+device prefixing of
    # has_entity_name entities that register while the device is in an area.
    _platform: str | None = None
    _object_id_key: str | None = None

    def __init__(
        self,
        coordinator: ShellyAdvancedCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        client_mac = coordinator.data.client_mac if coordinator.data else None
        name, device, device_info = _resolve_client_device(
            coordinator.hass, entry, client_mac or ""
        )
        if device is not None:
            self.device_entry = device
        else:
            self._attr_device_info = device_info
        if name and self._platform and self._object_id_key:
            self.entity_id = (
                f"{self._platform}.{slugify(name)}_{self._object_id_key}"
            )
