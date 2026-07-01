"""Coordinator for the Shelly Advanced integration.

Each poll:
  1. Probe the client Shelly directly on the main network (its own mDNS name
     on the direct port). If it answers, that is the truth.
  2. Otherwise find it behind an extender via its AP-client table (matching our
     MAC → forwarded port "mport"). A specific extender can be configured, or
     all other Shellies are scanned to auto-detect it.
  3. If reachable, update the client's `shelly` config entry host+port to match
     and reload it — but only when it actually needs it, so we don't fight HA's
     own zeroconf discovery (which rewrites the host but never the port).
  4. When reachable, also read the device's eco-mode / AP / range-extender
     config so the configuration switches reflect (and can change) it.

Credentials are resolved per host from the `shelly` config entries, so this
keeps working if auth is enabled later (Gen2+ digest, username "admin").
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import Credentials, ShellyRpc
from .const import (
    CONF_CLIENT_DIRECT_HOST,
    CONF_CLIENT_ENTRY_ID,
    CONF_DIRECT_PORT,
    CONF_EXTENDER_HOST,
    CONF_FOLLOW_ENABLED,
    CONF_SCAN_INTERVAL,
    DEFAULT_DIRECT_PORT,
    DEFAULT_FOLLOW_ENABLED,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SHELLY_DOMAIN,
    VIA_DIRECT,
    VIA_EXTENDER,
    VIA_UNREACHABLE,
)
from .models import ShellyLink

_LOGGER = logging.getLogger(__name__)


def _normalize_mac(mac: str | None) -> str:
    """Reduce any MAC representation to lowercase hex with no separators."""
    return "".join(c for c in (mac or "").lower() if c in "0123456789abcdef")


class ShellyAdvancedCoordinator(DataUpdateCoordinator[ShellyLink]):
    """Poll reachability + device config and keep the entry in sync."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator from a config entry."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        # Rebuilt each poll with current credentials; reused by the switches.
        self._rpc = ShellyRpc(hass)
        # Persisted across polls so the sensor can show when we last repointed.
        self.last_reconfigure: str | None = None
        # Whether auto-follow is active. Read once here (and re-read on reload)
        # so the very first poll after setup already honors the persisted
        # choice. Toggled at runtime by the per-entry switch.
        self.follow_enabled: bool = entry.options.get(
            CONF_FOLLOW_ENABLED, DEFAULT_FOLLOW_ENABLED
        )
        # In auto mode (no extender configured), the extender we last found the
        # client behind — probed first before rescanning all Shellies.
        self._last_extender_host: str | None = None

    @property
    def _client_entry_id(self) -> str:
        return self.config_entry.data[CONF_CLIENT_ENTRY_ID]

    @property
    def _direct_host(self) -> str:
        return self.config_entry.data[CONF_CLIENT_DIRECT_HOST]

    @property
    def _extender_host(self) -> str:
        return self.config_entry.data[CONF_EXTENDER_HOST]

    @property
    def _direct_port(self) -> int:
        return self.config_entry.options.get(CONF_DIRECT_PORT, DEFAULT_DIRECT_PORT)

    def _client_entry(self) -> ConfigEntry | None:
        return self.hass.config_entries.async_get_entry(self._client_entry_id)

    def _build_rpc(self) -> ShellyRpc:
        """Build an RPC client with per-host credentials from `shelly` entries."""
        creds_by_host: dict[str, Credentials] = {}
        for entry in self.hass.config_entries.async_entries(SHELLY_DOMAIN):
            host = entry.data.get(CONF_HOST)
            if host:
                creds_by_host[host] = (
                    entry.data.get(CONF_USERNAME),
                    entry.data.get(CONF_PASSWORD),
                )
        client = self._client_entry()
        default: Credentials = (
            (client.data.get(CONF_USERNAME), client.data.get(CONF_PASSWORD))
            if client
            else (None, None)
        )
        # The direct (mDNS) host and a pinned extender host may not match any
        # entry's stored host, so fall them back to the client's credentials.
        creds_by_host.setdefault(self._direct_host, default)
        if self._extender_host:
            creds_by_host.setdefault(self._extender_host, default)
        return ShellyRpc(self.hass, creds_by_host, default)

    async def _async_update_data(self) -> ShellyLink:
        client = self._client_entry()
        if client is None:
            raise UpdateFailed("Client Shelly config entry no longer exists")

        self._rpc = self._build_rpc()
        client_mac = _normalize_mac(client.unique_id)
        link = await self._probe(client_mac)

        if link.via != VIA_UNREACHABLE:
            # Only repoint the entry when auto-follow is enabled.
            if self.follow_enabled:
                await self._apply(client, link)
            # Read device config so the switches reflect current state.
            await self._read_config(link)

        link.client_mac = client_mac
        link.last_reconfigure = self.last_reconfigure
        return link

    async def _probe(self, client_mac: str) -> ShellyLink:
        """Determine how the client Shelly is reachable right now."""
        # 1) Direct on the main network, via its own stable mDNS name.
        status = await self._rpc.wifi_status(self._direct_host, self._direct_port)
        if status is not None:
            return ShellyLink(
                via=VIA_DIRECT,
                host=self._direct_host,
                port=self._direct_port,
                ssid=status.get("ssid"),
                ip=status.get("sta_ip") or status.get("ip"),
            )

        # 2) Behind an extender: locate our MAC in an extender's AP-client
        #    table and read the forwarded port ("mport") it assigned to us.
        if self._extender_host:
            # A specific extender was configured — just query that one.
            return await self._find_on_extender(
                self._extender_host, client_mac
            ) or ShellyLink(via=VIA_UNREACHABLE)

        # Auto mode (no extender configured): search every other Shelly's
        # AP-client table to find whichever one is currently extending us.
        # Try the last extender we found first (cheap), then scan the rest
        # concurrently. Non-extender Shellies just return an empty list.
        if self._last_extender_host:
            link = await self._find_on_extender(
                self._last_extender_host, client_mac
            )
            if link is not None:
                return link

        candidates = self._other_shelly_hosts(exclude=self._last_extender_host)
        results = await asyncio.gather(
            *(self._find_on_extender(host, client_mac) for host in candidates)
        )
        for link in results:
            if link is not None:
                return link

        return ShellyLink(via=VIA_UNREACHABLE)

    def _other_shelly_hosts(self, exclude: str | None = None) -> list[str]:
        """Return the hosts of all other Shelly entries (potential extenders)."""
        hosts: list[str] = []
        seen: set[str] = {exclude} if exclude else set()
        for entry in self.hass.config_entries.async_entries(SHELLY_DOMAIN):
            if entry.entry_id == self._client_entry_id:
                continue
            host = entry.data.get(CONF_HOST)
            if host and host not in seen:
                seen.add(host)
                hosts.append(host)
        return hosts

    async def _find_on_extender(
        self, extender_host: str, client_mac: str
    ) -> ShellyLink | None:
        """Return an extender ShellyLink if the client is behind this host."""
        for candidate in await self._rpc.ap_clients(extender_host) or []:
            if _normalize_mac(candidate.get("mac")) != client_mac:
                continue
            mport = candidate.get("mport") or candidate.get("port")
            if mport:
                # Remember it so we probe it first next time.
                self._last_extender_host = extender_host
                return ShellyLink(
                    via=VIA_EXTENDER,
                    host=extender_host,
                    port=int(mport),
                    ip=candidate.get("ip"),
                    mport=int(mport),
                )
            _LOGGER.warning(
                "Client %s is connected to extender %s but the AP-client entry "
                "carries no forwarded port: %s",
                client_mac,
                extender_host,
                candidate,
            )
        return None

    async def _read_config(self, link: ShellyLink) -> None:
        """Populate eco-mode / AP / range-extender state from the device."""
        wifi = await self._rpc.call(link.host, link.port, "WiFi.GetConfig")
        if wifi is not None:
            ap = wifi.get("ap") or {}
            link.ap_enabled = ap.get("enable")
            range_extender = ap.get("range_extender") or {}
            link.extender_enabled = range_extender.get("enable")
        sys = await self._rpc.call(link.host, link.port, "Sys.GetConfig")
        if sys is not None:
            link.eco_mode = (sys.get("device") or {}).get("eco_mode")

    def _endpoint(self) -> tuple[str, int] | None:
        """Return the currently reachable (host, port), or None."""
        data = self.data
        if data and data.via != VIA_UNREACHABLE and data.host and data.port:
            return (data.host, data.port)
        return None

    async def async_set_device_config(self, method: str, config: dict) -> None:
        """Apply a *.SetConfig on the reachable endpoint, then refresh."""
        endpoint = self._endpoint()
        if endpoint is None:
            _LOGGER.warning("Cannot set config: %s is unreachable", self.config_entry.title)
            return
        await self._rpc.call(*endpoint, method, {"config": config})
        await self.async_request_refresh()

    async def _apply(self, client: ConfigEntry, link: ShellyLink) -> None:
        """Repoint the client `shelly` entry to the reachable endpoint.

        Shelly does not reload on a data change (it only reads host/port at
        setup), so we must reload the entry ourselves after updating it.
        """
        cur_host = client.data.get(CONF_HOST)
        cur_port = client.data.get(CONF_PORT, DEFAULT_DIRECT_PORT)
        loaded = client.state is ConfigEntryState.LOADED

        if link.via == VIA_DIRECT:
            # Tolerate zeroconf host churn: whether the entry holds the mDNS
            # name or the raw IP, both work on the direct port. Only intervene
            # when the port is wrong (the classic bug) or the entry is not
            # loaded — otherwise we would ping-pong against discovery.
            if loaded and cur_port == link.port:
                return
        elif loaded and cur_host == link.host and cur_port == link.port:
            return

        new_data = {**client.data, CONF_HOST: link.host, CONF_PORT: link.port}
        if not self.hass.config_entries.async_update_entry(client, data=new_data):
            return

        _LOGGER.info(
            "Repointed %s to %s:%s (reachable via %s)",
            client.title,
            link.host,
            link.port,
            link.via,
        )
        self.last_reconfigure = dt_util.utcnow().isoformat()
        await self.hass.config_entries.async_reload(client.entry_id)
