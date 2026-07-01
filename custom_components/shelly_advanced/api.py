"""Minimal async client for the Shelly Gen2+ RPC endpoints we rely on.

Auth mirrors the core `shelly` integration: Gen2+ devices use HTTP digest auth
once a password is set (username defaults to "admin"). Credentials are resolved
per host so this keeps working if you enable auth later — including when
scanning other Shellies that may have their own password.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import DigestAuthMiddleware

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import HTTP_TIMEOUT, RPC_WIFI_AP_CLIENTS, RPC_WIFI_STATUS

_LOGGER = logging.getLogger(__name__)

# (username, password); empty password means unauthenticated.
Credentials = tuple[str | None, str | None]


class ShellyRpc:
    """Tiny wrapper around the Shelly RPC calls we need, with optional auth."""

    def __init__(
        self,
        hass: HomeAssistant,
        creds_by_host: dict[str, Credentials] | None = None,
        default_creds: Credentials = (None, None),
    ) -> None:
        """Store HA's shared session and per-host credentials."""
        self._session = async_get_clientsession(hass)
        self._creds_by_host = creds_by_host or {}
        self._default_creds = default_creds

    def _kwargs(self, host: str) -> dict[str, Any]:
        """Return per-request kwargs, adding digest auth when a password is set."""
        username, password = self._creds_by_host.get(host, self._default_creds)
        if password:
            return {
                "middlewares": (
                    DigestAuthMiddleware(
                        login=username or "admin", password=password
                    ),
                )
            }
        return {}

    async def _get_json(self, host: str, url: str) -> Any | None:
        try:
            async with asyncio.timeout(HTTP_TIMEOUT):
                resp = await self._session.get(url, **self._kwargs(host))
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Shelly GET %s failed: %s", url, err)
            return None

    async def wifi_status(self, host: str, port: int) -> dict | None:
        """Return WiFi.GetStatus for a device, or None if unreachable."""
        return await self._get_json(host, f"http://{host}:{port}{RPC_WIFI_STATUS}")

    async def ap_clients(self, host: str, port: int = 80) -> list[dict] | None:
        """Return the extender's AP client list, or None if unreachable."""
        data = await self._get_json(
            host, f"http://{host}:{port}{RPC_WIFI_AP_CLIENTS}"
        )
        if data is None:
            return None
        return data.get("ap_clients", [])

    async def call(
        self,
        host: str,
        port: int,
        method: str,
        params: dict | None = None,
    ) -> dict | None:
        """Make a JSON-RPC call to /rpc; return the ``result`` dict or None."""
        url = f"http://{host}:{port}/rpc"
        payload = {"id": 1, "method": method, "params": params or {}}
        try:
            async with asyncio.timeout(HTTP_TIMEOUT):
                resp = await self._session.post(
                    url, json=payload, **self._kwargs(host)
                )
                resp.raise_for_status()
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            _LOGGER.debug("Shelly RPC %s on %s failed: %s", method, host, err)
            return None
        if not isinstance(data, dict):
            return None
        if "error" in data:
            _LOGGER.debug("Shelly RPC %s on %s error: %s", method, host, data["error"])
            return None
        return data.get("result")
