# Agent instructions

## Project

This Home Assistant integration keeps a roaming Shelly device's config entry pointed at its currently reachable endpoint, including when the device is reached through a Wi-Fi extender.

## Working in this repository

- Read `README.md` before changing discovery, endpoint selection, or forwarded-port behavior.
- Keep direct-device and extender-proxy probing ordered as documented, and do not add network details for a user's installation to this guide.
- Before changing CI, check [pschmitt/ci-workflows](https://github.com/pschmitt/ci-workflows) for reusable components and preserve this repository's existing checks.

## Validation

- Run `uvx ruff check .` and `uvx ruff format --check .` for Python changes.
- CI runs Hassfest and the shared Ruff checks; it currently has no test job.
