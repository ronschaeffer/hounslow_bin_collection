# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.11] - 2026-04-07

### Fixed
- Lint cleanup on `integrations/mqtt.py` (ruff I001 import sort) that broke
  the v0.1.10 GHCR build.

## [0.1.10] - 2026-04-07

### Added
- MQTT-aware healthcheck via `ha_mqtt_publisher` v0.4.0's shared `HeartbeatFile`.
  After every successful `BinCollectionMQTTPublisher.publish_bin_data()` run,
  touches `/app/storage/.mqtt_heartbeat` (path overridable via
  `MQTT_HEARTBEAT_PATH` env var).
- Dockerfile `HEALTHCHECK` now runs
  `python -m ha_mqtt_publisher.healthcheck_cli --heartbeat /app/storage/.mqtt_heartbeat --max-age 90000`,
  which exits non-zero when the heartbeat is stale or missing. The container
  previously had **no healthcheck at all** because it's cron-driven and has
  no HTTP endpoint.
- New `/app/storage` directory in the Dockerfile for the heartbeat file.

### Changed
- Bumped `ha-mqtt-publisher` to `>=0.4.0`.
- **Breaking**: requires a new `/app/storage` bind mount on existing
  deployments — without it, the heartbeat lands in the writable container
  layer and gets wiped on every recreate, causing the healthcheck to perma-fail.
  The Unraid template at `unraid-template/` includes this mount.

### Why
Addresses the failure mode observed on 2026-04-07 where the EMQX broker
crash-looped for hours and `HounslowBinCollection` kept reporting "Up" with
MQTT silently broken because the container had no healthcheck. Now a missed
daily run is detectable from `docker ps` and from any monitoring tool that
reads container health.

## [0.1.0] - 2026-04-01

Initial release.

### Added
- Browser automation via Playwright to scrape Hounslow Council waste collection schedules
- Smart address matching with abbreviation expansion (Rd->Road, St->Street, etc.)
- MQTT publishing with Home Assistant auto-discovery (ha-mqtt-publisher)
- Per-waste-type sensors: Black Bin, Recycling, Food Waste, Garden Waste
- Consolidated `next_waste_collection` sensor with scheduled/icon/icon_color attributes
- Diagnostic sensors: Last Run, Last Run Status, Council Page Accessible, Collection Types Found, Software Version
- Refresh button for on-demand collection
- ICS calendar generation with evening and morning reminders
- Lightweight HTTP server for serving ICS files (Remote Calendar integration)
- CLI entry point (`hounslow-bins`) with subcommands: collect, mqtt, calendar, all, status, serve
- Multi-stage Dockerfile with Playwright/Chromium and cron scheduling
- Unraid community template
- Mushroom template card for HA dashboard
- CI: lint, test, code-quality, docker-publish, local-consistency, version-bump workflows
- Makefile with standard targets (check, fix, test, ci-check)
- Pre-commit hooks with ruff, codespell, pre-push pytest
