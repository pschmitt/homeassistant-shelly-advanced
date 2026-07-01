"""Config and options flow for the Shelly Extender Follow integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import ShellyRpc
from .const import (
    CONF_CLIENT_DIRECT_HOST,
    CONF_CLIENT_ENTRY_ID,
    CONF_DIRECT_PORT,
    CONF_EXTENDER_HOST,
    CONF_SCAN_INTERVAL,
    DEFAULT_DIRECT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)


class ShellyExtenderFollowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Pick the client Shelly, its direct host, and the extender host."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client_entry_id = user_input[CONF_CLIENT_ENTRY_ID]
            client = self.hass.config_entries.async_get_entry(client_entry_id)
            if client is None or not client.unique_id:
                errors["base"] = "invalid_client"
            else:
                await self.async_set_unique_id(client_entry_id)
                self._abort_if_unique_id_configured()
                # Confirm the extender is reachable before committing.
                rpc = ShellyRpc(self.hass)
                if await rpc.ap_clients(user_input[CONF_EXTENDER_HOST]) is None:
                    errors["base"] = "cannot_connect_extender"
                else:
                    return self.async_create_entry(
                        title=f"Follow: {client.title}",
                        data={
                            CONF_CLIENT_ENTRY_ID: client_entry_id,
                            CONF_CLIENT_DIRECT_HOST: user_input[
                                CONF_CLIENT_DIRECT_HOST
                            ],
                            CONF_EXTENDER_HOST: user_input[CONF_EXTENDER_HOST],
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ENTRY_ID): selector.ConfigEntrySelector(
                    selector.ConfigEntrySelectorConfig(integration="shelly")
                ),
                vol.Required(CONF_CLIENT_DIRECT_HOST): str,
                vol.Required(CONF_EXTENDER_HOST): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return ShellyExtenderFollowOptionsFlow()


class ShellyExtenderFollowOptionsFlow(OptionsFlow):
    """Tune the poll interval and direct port."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Show and persist the options."""
        if user_input is not None:
            # Preserve options not shown here (e.g. follow_enabled, which is
            # owned by the per-entry switch) so saving does not reset them.
            return self.async_create_entry(
                data={**self.config_entry.options, **user_input}
            )

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                vol.Optional(
                    CONF_DIRECT_PORT,
                    default=opts.get(CONF_DIRECT_PORT, DEFAULT_DIRECT_PORT),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
