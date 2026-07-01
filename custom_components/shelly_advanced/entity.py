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
) -> tuple[str | None, DeviceInfo]:
    """Return (device_name, DeviceInfo) linking to the client Shelly's device.

    We attach to the existing Shelly device (reusing its identifiers/
    connections) so our entities appear on its page and the device lists both
    integrations. The name is used to build clean entity_ids (see the base
    entity) that match the Shelly's own convention.
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
    if device is not None:
        return (
            device.name_by_user or device.name,
            DeviceInfo(
                identifiers=set(device.identifiers),
                connections=set(device.connections),
            ),
        )
    if client_mac:
        return (
            None,
            DeviceInfo(
                connections={(dr.CONNECTION_NETWORK_MAC, dr.format_mac(client_mac))}
            ),
        )
    return (
        entry.title,
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
        name, device_info = _resolve_client_device(
            coordinator.hass, entry, client_mac or ""
        )
        self._attr_device_info = device_info
        if name and self._platform and self._object_id_key:
            self.entity_id = (
                f"{self._platform}.{slugify(name)}_{self._object_id_key}"
            )
