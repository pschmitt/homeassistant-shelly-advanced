"""Per-Shelly switch to enable or disable automatic follow.

When off, the integration keeps polling and updating the reachability sensor
but stops repointing the client `shelly` config entry — useful while doing
manual maintenance on the device or its config entry.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_FOLLOW_ENABLED, DOMAIN
from .coordinator import ShellyExtenderFollowCoordinator
from .entity import ShellyExtenderFollowEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the auto-follow switch."""
    coordinator: ShellyExtenderFollowCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FollowEnabledSwitch(coordinator, entry)])


class FollowEnabledSwitch(ShellyExtenderFollowEntity, SwitchEntity):
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
