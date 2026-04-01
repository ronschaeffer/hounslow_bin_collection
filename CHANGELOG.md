# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
