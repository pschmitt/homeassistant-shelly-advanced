"""Constants for the Shelly Extender Follow integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "shelly_extender_follow"
PLATFORMS: list[Platform] = [Platform.SENSOR]

# Config (entry.data)
CONF_CLIENT_ENTRY_ID = "client_entry_id"
CONF_CLIENT_DIRECT_HOST = "client_direct_host"
CONF_EXTENDER_HOST = "extender_host"

# Options (entry.options)
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DIRECT_PORT = "direct_port"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
DEFAULT_DIRECT_PORT = 80

# Reachability classification — also the sensor state (an ENUM).
VIA_DIRECT = "direct"
VIA_EXTENDER = "extender"
VIA_UNREACHABLE = "unreachable"

# Sensor state attributes.
ATTR_HOST = "host"
ATTR_PORT = "port"
ATTR_SSID = "ssid"
ATTR_IP = "ip"
ATTR_MPORT = "mport"
ATTR_CLIENT_MAC = "client_mac"
ATTR_LAST_RECONFIGURE = "last_reconfigure"

# Shelly Gen2+ RPC endpoints (served over HTTP on the device).
RPC_WIFI_STATUS = "/rpc/WiFi.GetStatus"
RPC_WIFI_AP_CLIENTS = "/rpc/WiFi.ListAPClients"

HTTP_TIMEOUT = 5
