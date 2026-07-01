# Shelly Extender Follow

A Home Assistant integration that keeps a **roaming Shelly**'s `shelly` config
entry pointed at wherever the device is actually reachable.

Some Shelly devices roam between two networks:

- **Direct** — on the main network they answer on their own mDNS name at the
  normal HTTP port (usually `:80`).
- **Via an extender** — when they fall back behind another Shelly running the
  Gen2+ **WiFi range extender** function, they are only reachable through that
  Shelly's port-forward on a dynamically assigned port (`mport`).

When the device roams, Home Assistant's own zeroconf discovery rewrites the
config entry's **host** but leaves the **port** stale — so the entry ends up
pointing at, say, the direct IP on the *extender* port and goes into
`setup_retry`. This integration fixes that.

## How it works

Every poll it:

1. Probes the client Shelly directly (`WiFi.GetStatus` on its mDNS name +
   direct port). If it answers, that endpoint wins.
2. Otherwise queries the extender's `WiFi.ListAPClients`, matches the client's
   MAC, and reads the forwarded port (`mport`) it was assigned.
3. If the reachable endpoint differs from the client entry's current
   host+port, it updates the entry **and reloads it** (Shelly does not reload
   on a data change by itself). In direct mode it tolerates zeroconf's host
   churn and only intervenes when the port is wrong or the entry failed to
   load, so it never ping-pongs against discovery.

It exposes one `sensor` per configured device whose state is `direct`,
`extender`, or `unreachable`, with the resolved `host`/`port`/`ssid`/`ip`/
`mport`/`client_mac` and the `last_reconfigure` timestamp as attributes.

## Configuration

Add the integration from the UI and provide:

- **Client Shelly** — the roaming `shelly` config entry to keep in sync.
- **Client direct host** — the mDNS name it answers on when on the main
  network (e.g. `shelly-master-bathroom-ventilation.lan`).
- **Extender host** — the Shelly acting as the range extender
  (e.g. `shelly-master-bathroom-towel-heater.lan`).

Options: poll interval (default 30 s) and direct port (default 80).
