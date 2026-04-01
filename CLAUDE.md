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
  models.py              # Dataclasses: AddressConfig, BinCollectionData, CollectionInfo
  collector.py           # HounslowBinCollector - high-level interface wrapping BrowserWasteCollector
  browser_collector.py   # BrowserWasteCollector - Playwright automation against council website
  enhanced_extractor.py  # HounslowDataExtractor - parses collection data from page content
  integrations/
    mqtt.py              # BinCollectionMQTTPublisher - uses ha_mqtt_publisher library for HA discovery
    calendar.py          # BinCollectionCalendar - generates ICS files with reminders
```

**Data flow:** CLI/scheduler -> `HounslowBinCollector.collect_bin_data()` -> `BrowserWasteCollector` (Playwright navigates council site iframe, enters postcode, selects address) -> `HounslowDataExtractor` parses results -> `BinCollectionData` model -> published to MQTT and/or written as ICS.

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
