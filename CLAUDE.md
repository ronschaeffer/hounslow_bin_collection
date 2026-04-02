# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Hounslow Bin Collection scrapes waste collection schedules from the London Borough of Hounslow council website using Playwright browser automation (the council's API is blocked). It publishes results via MQTT (for Home Assistant) and generates ICS calendar files. Deployed as a Docker container on Unraid.

## Commands

```bash
poetry install --with dev     # install all deps including dev
make check                    # lint only (ruff)
make fix                      # lint + format (ruff)
make test                     # run pytest
make ci-check                 # lint + test (run before pushing)
make install-hooks            # install pre-commit hooks
make clean                    # remove __pycache__, .pytest_cache, .ruff_cache
```

Run a single test file: `poetry run pytest tests/test_models.py`
Run a single test: `poetry run pytest tests/test_models.py::test_foo -v`

## Architecture

```
src/hounslow_bin_collection/
  __init__.py            # Package exports and version
  __main__.py            # CLI entry point (argparse subcommands: collect, mqtt, calendar, all, status)
  version.py             # Dynamic version management
  config.py              # Config from YAML + env vars (dot-notation access, env overrides)
  models.py              # Dataclasses + fill_recycling_food_dates() date inference
  collector.py           # HounslowBinCollector - high-level interface wrapping BrowserWasteCollector
  browser_collector.py   # BrowserWasteCollector - Playwright automation against council website
  enhanced_extractor.py  # HounslowDataExtractor - parses collection data from page content
  integrations/
    mqtt.py              # BinCollectionMQTTPublisher - uses ha_mqtt_publisher library for HA discovery
    calendar.py          # BinCollectionCalendar - generates ICS files with reminders
```

**Data flow:** CLI/scheduler -> `HounslowBinCollector.collect_bin_data()` -> `BrowserWasteCollector` (Playwright navigates council site iframe, enters postcode, selects address) -> `HounslowDataExtractor` parses results -> `BinCollectionData` model -> published to MQTT and/or written as ICS.

**Date inference:** Recycling and food waste are collected on every collection day (same day as black bin or garden waste). If the scraper misses these dates, `fill_recycling_food_dates()` in `models.py` fills them from companion types. Extrapolation is limited to 7 days past a scheduled black bin collection. The `next_waste_collection` sensor shows whichever of black bin, garden waste, or recycling is genuinely soonest (food waste is never the headline).

**Key external dependency:** `ha-mqtt-publisher` (PyPI) provides `MQTTPublisher`, `Device`, `Sensor`, and `publish_discovery_configs`.

## Code standards

- Python >=3.11
- Ruff: line-length 88, double quotes, lf line endings, isort with `force-sort-within-sections`
- Pre-commit: pre-commit-hooks v5.0.0, ruff-pre-commit v0.12.7, codespell v2.2.6
- Makefile targets: check / fix / test / ci-check / install-hooks / clean
- No f-strings in logging calls (G004 enforced)
- Type hints on all public API
- Address matching uses abbreviation expansion (Rd->Road, St->Street, etc.) in `normalize_address_for_matching()`

## Configuration

Config priority: environment variables > YAML file (`config/config.yaml`). Key env vars:
- `HOUNSLOW_POSTCODE` / `HOUNSLOW_ADDRESS` - required for browser automation
- `MQTT_BROKER_URL` / `MQTT_ENABLED` - MQTT integration
- `CALENDAR_ENABLED` - ICS generation

## Testing notes

Tests use `pytest` with `--strict-markers` and `--strict-config`. Markers: `slow`, `integration`. Coverage targets `src/`. Browser-dependent tests require Playwright browsers installed (`playwright install chromium`).

## Workflow

- Run `make fix` before committing
- Run `make ci-check` before pushing

## "Ship it" — full deploy workflow

When the user says **"ship it"**, run the full end-to-end cycle:

1. **Test:** Clone fresh on Python Workspace (`/tmp/hounslow_test`), `poetry install --with dev`, `poetry run pytest tests/ -v`
2. **Commit & push:** `make fix`, commit changes, push to main
3. **Tag & build:** Increment latest `v0.x.y` tag, push tag to trigger `docker-publish.yml` on GitHub Actions
4. **Deploy:** Use Unraid MCP `update_container` (force=true) on `HounslowBinCollection`
5. **Verify:** `docker exec HounslowBinCollection hounslow-bins all`, then check HA entities via `ha_search_entities` for `hounslow_bins` (this project has HA integration)
6. **Docs:** Update README, CLAUDE.md, and Obsidian note (`🏡 Personal/Making & Homelab/Coding/Hounslow Bin Collection.md`)

Key details:
- Python Workspace needs `export PATH="$HOME/.local/bin:$PATH"` for poetry
- Container: `HounslowBinCollection`, image `ghcr.io/ronschaeffer/hounslow_bin_collection:latest`, port 8208:8080
- HA entities all prefixed `hounslow_bins_`
