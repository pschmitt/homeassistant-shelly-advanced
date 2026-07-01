"""Minimal async client for the Shelly Gen2+ RPC endpoints we rely on."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import HTTP_TIMEOUT, RPC_WIFI_AP_CLIENTS, RPC_WIFI_STATUS

_LOGGER = logging.getLogger(__name__)


class ShellyRpc:
    """Tiny wrapper around the two unauthenticated RPC calls we need."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Store HA's shared aiohttp session."""
        self._session = async_get_clientsession(hass)

    async def _get(self, url: str) -> Any | None:
        """GET a JSON RPC endpoint, returning None on any failure."""
        try:
            async with asyncio.timeout(HTTP_TIMEOUT):
                resp = await self._session.get(url)
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Shelly RPC GET %s failed: %s", url, err)
            return None

    async def wifi_status(self, host: str, port: int) -> dict | None:
        """Return WiFi.GetStatus for a device, or None if unreachable."""
        return await self._get(f"http://{host}:{port}{RPC_WIFI_STATUS}")

    async def ap_clients(self, host: str) -> list[dict] | None:
        """Return the extender's AP client list, or None if unreachable.

        An empty list means "reachable, but no clients connected"; None means
        the extender itself could not be queried.
        """
        data = await self._get(f"http://{host}{RPC_WIFI_AP_CLIENTS}")
        if data is None:
            return None
        return data.get("ap_clients", [])
