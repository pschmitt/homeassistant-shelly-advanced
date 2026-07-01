"""Data models for the Shelly Advanced integration."""

from __future__ import annotations

from dataclasses import dataclass

from .const import VIA_UNREACHABLE


@dataclass(slots=True)
class ShellyLink:
    """Where the client Shelly is currently reachable, and what we applied.

    Produced fresh each poll by the coordinator and consumed by the sensor.
    """

    via: str = VIA_UNREACHABLE
    host: str | None = None
    port: int | None = None
    ssid: str | None = None
    ip: str | None = None
    # The forwarded port the extender assigned to the client (Gen2+ range
    # extender "mport"). Only set when reachable via the extender.
    mport: int | None = None
    client_mac: str | None = None
    # ISO timestamp of the last time we actually repointed the client entry.
    last_reconfigure: str | None = None
    # Device config, read when reachable (None = unknown / feature absent).
    eco_mode: bool | None = None
    ap_enabled: bool | None = None
    extender_enabled: bool | None = None
