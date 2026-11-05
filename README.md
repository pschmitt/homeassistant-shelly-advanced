<p align="center">
  <img src="custom_components/shelly_advanced/brand/logo.png" width="128" alt="Shelly Advanced logo">
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/marketplace_repository/?owner=pschmitt&amp;repository=homeassistant-shelly-advanced&amp;category=integration"><img src="https://my.home-assistant.io/badges/marketplace_repository.svg" alt="Open this integration in Home Assistant Marketplace"></a>
</p>

<h1 align="center">Shelly Advanced</h1>

<p align="center">Keep a roaming Shelly integration pointed at its reachable host and port.</p>

Home Assistant's zeroconf discovery can update a roaming device's host without
updating its port. This integration follows the device between direct access
and an extender's forwarded port. See [Shelly roaming](docs/roaming.md).

## Features

- **Direct-first probing:** Prefer a device's own endpoint and fall back to its range extender.
- **Extender discovery:** Find the current extender automatically or configure a specific host.
- **Automatic repair:** Update and reload the original `shelly` config entry when its reachable host or port changes.
- **Per-device controls:** Show reachability and toggle auto-follow for each Shelly.

## Install

Use the Marketplace badge above on Home Assistant 2026.11 or later to add this
repository as a custom integration. On older versions, add it as a HACS
custom repository of type **Integration**. Install and restart Home Assistant.
The badge does not imply a public catalog listing.

## Quick start

1. Add **Shelly Advanced** under **Settings → Devices & services → Add integration**.
2. Select a Shelly to follow, or discover multiple devices.
3. Enter its direct hostname; leave the extender blank for auto-discovery.
4. Inspect the device's Reachability sensor as it changes networks.

## Documentation

| Topic | Description |
|-------|-------------|
| [Shelly roaming](docs/roaming.md) | Direct and extender probing, config-entry updates and options |
