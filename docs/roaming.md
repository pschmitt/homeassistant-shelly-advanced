# Shelly roaming

Some Shelly devices roam between a directly reachable network and another
Shelly acting as a Gen2+ Wi-Fi range extender. Direct access uses the device's
mDNS name and normal HTTP port (usually 80); extender access uses a dynamically
assigned forwarded port (`mport`). Home Assistant's zeroconf discovery may
rewrite the `shelly` config entry's host without updating its port, leaving
that entry in `setup_retry`.

On each poll, the integration first probes the client directly using
`WiFi.GetStatus`. If the device answers, that endpoint wins. Otherwise it
queries `WiFi.ListAPClients` on a configured extender, or scans other Shellies
and matches the client's MAC to discover its current extender. The last match
is tried first on subsequent polls.

If the reachable host and port differ from the config entry, the integration
updates and reloads it. In direct mode it tolerates zeroconf host changes and
intervenes only when the port is wrong or the entry failed to load.

## Configuration

Add **Shelly Advanced** from Home Assistant's integration UI. Choose one
`shelly` config entry and its direct mDNS hostname (such as
`shelly-device.example.com`), or discover and select multiple Shellies. An
extender host is optional; leave it empty to scan other Shellies when direct
access fails. A non-roaming device stays on its direct endpoint.

Each followed device gets a **Reachability** sensor (`direct`, `extender` or
`unreachable`) and an **Auto-follow** switch. The sensor includes resolved
`host`, `port`, `ssid`, `ip`, `mport`, `client_mac` and `last_reconfigure`
attributes. The poll interval defaults to 30 seconds and the direct port to
80; both are configurable per entry.
