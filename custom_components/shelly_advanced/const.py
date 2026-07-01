"""Constants for the Shelly Advanced integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "shelly_advanced"
# The core integration whose config entries we follow.
SHELLY_DOMAIN = "shelly"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

# Config-flow field for bulk discovery (multi-select of client entries).
CONF_SELECTED_CLIENTS = "selected_clients"

# Config (entry.data)
CONF_CLIENT_ENTRY_ID = "client_entry_id"
CONF_CLIENT_DIRECT_HOST = "client_direct_host"
CONF_EXTENDER_HOST = "extender_host"

# Options (entry.options)
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DIRECT_PORT = "direct_port"
# Whether the integration actively repoints the client entry. Toggled at
# runtime by the per-entry "Auto-follow" switch; persisted here so the choice
# survives restarts and is respected on the very first poll after setup.
CONF_FOLLOW_ENABLED = "follow_enabled"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
DEFAULT_DIRECT_PORT = 80
DEFAULT_FOLLOW_ENABLED = True

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
