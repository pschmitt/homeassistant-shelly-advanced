"""Switches for the Shelly Advanced integration.

- Auto-follow: whether the integration repoints the client `shelly` entry
  (an integration setting, persisted in options).
- Eco mode / AP / Range extender: the device's own config, read and written
  live on whatever endpoint the device is currently reachable on.

All are configuration-category entities.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_FOLLOW_ENABLED, DOMAIN
from .coordinator import ShellyAdvancedCoordinator
from .entity import ShellyAdvancedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the auto-follow and device-config switches."""
    coordinator: ShellyAdvancedCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FollowEnabledSwitch(coordinator, entry),
            EcoModeSwitch(coordinator, entry),
            ApSwitch(coordinator, entry),
            RangeExtenderSwitch(coordinator, entry),
        ]
    )


class FollowEnabledSwitch(ShellyAdvancedEntity, SwitchEntity):
    """Toggle whether this client Shelly's config entry is auto-repointed."""

    _attr_translation_key = "follow_enabled"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self) -> str:
        """Return a stable unique id derived from the config entry."""
        return f"{self._entry.entry_id}_follow_enabled"

    @property
    def is_on(self) -> bool:
        """Return whether auto-follow is currently enabled."""
        return self.coordinator.follow_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable auto-follow."""
        await self._persist(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable auto-follow."""
        await self._persist(False)

    async def _persist(self, value: bool) -> None:
        """Persist the choice to options; the update listener reloads the entry.

        Storing it in options (rather than only in memory) means the setting
        survives restarts and is honored on the first poll after setup.
        """
        self.coordinator.follow_enabled = value
        self.async_write_ha_state()
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_FOLLOW_ENABLED: value},
        )


class _DeviceConfigSwitch(ShellyAdvancedEntity, SwitchEntity):
    """Base for switches backed by the device's own config over RPC.

    Unavailable when the value is unknown — device unreachable, or the feature
    is not present on this model.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _key: str
    _method: str

    def __init__(
        self, coordinator: ShellyAdvancedCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize with the subclass translation key."""
        super().__init__(coordinator, entry)
        self._attr_translation_key = self._key

    @property
    def unique_id(self) -> str:
        """Return a stable unique id derived from the config entry."""
        return f"{self._entry.entry_id}_{self._key}"

    def _current(self) -> bool | None:
        """Return the current value from the coordinator, or None if unknown."""
        raise NotImplementedError

    def _config(self, value: bool) -> dict:
        """Return the SetConfig payload for the given value."""
        raise NotImplementedError

    @property
    def available(self) -> bool:
        """Available only when the device reported this setting."""
        return super().available and self._current() is not None

    @property
    def is_on(self) -> bool | None:
        """Return the current on/off state."""
        return self._current()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the setting on the device."""
        await self.coordinator.async_set_device_config(
            self._method, self._config(True)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the setting on the device."""
        await self.coordinator.async_set_device_config(
            self._method, self._config(False)
        )


class EcoModeSwitch(_DeviceConfigSwitch):
    """Toggle the device's eco mode (Sys.SetConfig device.eco_mode)."""

    _key = "eco_mode"
    _method = "Sys.SetConfig"

    def _current(self) -> bool | None:
        return self.coordinator.data.eco_mode if self.coordinator.data else None

    def _config(self, value: bool) -> dict:
        return {"device": {"eco_mode": value}}


class ApSwitch(_DeviceConfigSwitch):
    """Toggle the device's access-point (WiFi.SetConfig ap.enable)."""

    _key = "ap_enabled"
    _method = "WiFi.SetConfig"

    def _current(self) -> bool | None:
        return self.coordinator.data.ap_enabled if self.coordinator.data else None

    def _config(self, value: bool) -> dict:
        return {"ap": {"enable": value}}


class RangeExtenderSwitch(_DeviceConfigSwitch):
    """Toggle the device's WiFi range extender (ap.range_extender.enable)."""

    _key = "range_extender"
    _method = "WiFi.SetConfig"

    def _current(self) -> bool | None:
        return (
            self.coordinator.data.extender_enabled
            if self.coordinator.data
            else None
        )

    def _config(self, value: bool) -> dict:
        return {"ap": {"range_extender": {"enable": value}}}
