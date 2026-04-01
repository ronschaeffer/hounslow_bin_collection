# Hounslow Bin Collection

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Automated waste collection schedule scraper for the London Borough of Hounslow. Uses browser automation to extract real-time bin collection dates from the council website, publishes to MQTT for Home Assistant, and generates ICS calendar files.

---

## Table of Contents

1. [Features](#features)
2. [How It Works](#how-it-works)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [MQTT Topics](#mqtt-topics)
8. [Home Assistant Integration](#home-assistant-integration)
9. [Docker Deployment](#docker-deployment)
10. [Testing](#testing)
11. [Development](#development)
12. [License](#license)

---

## Features

- **Browser Automation:** Playwright-based scraping of the official Hounslow Council website
- **Smart Address Matching:** Abbreviation expansion (`Rd` to `Road`, `St` to `Street`, etc.) and fuzzy matching
- **MQTT Auto-Discovery:** Creates Home Assistant sensors for each waste type via retained discovery topics
- **Consolidated Sensor:** Single `next_waste_collection` sensor showing the soonest collection with urgency attributes, icon, and emoji
- **Diagnostic Sensors:** Last run timestamp, run status, council page accessibility (alerts if unreachable >24h), collection count, software version
- **Control Button:** Refresh button to trigger immediate collection from Home Assistant
- **ICS Calendar:** Generates calendar files with evening and morning reminders, served over HTTP for the [Remote Calendar](https://www.home-assistant.io/integrations/remote_calendar/) integration
- **Fully Containerized:** Docker image with Playwright/Chromium, built-in cron scheduler, and ICS web server

## How It Works

1. Navigates to Hounslow Council's waste collection form
2. Handles the cookie banner and "Before you begin" interstitial automatically
3. Enters your postcode, selects your address from the dropdown
4. Extracts collection types, frequencies, and next/last dates
5. Publishes to MQTT (Home Assistant discovery) and/or generates ICS calendar

Collection dates are extracted in real-time from the council's system, including holiday adjustments.

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- Chromium (installed automatically by Playwright)
- MQTT broker (optional, for Home Assistant integration)

## Installation

```bash
git clone https://github.com/ronschaeffer/hounslow_bin_collection.git
cd hounslow_bin_collection
poetry install --with dev
poetry run playwright install chromium
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `HOUNSLOW_POSTCODE` | Your Hounslow postcode | **Yes** | |
| `HOUNSLOW_ADDRESS` | Address hint for matching | **Yes** | |
| `MQTT_ENABLED` | Enable MQTT publishing | No | `true` |
| `MQTT_BROKER_URL` | MQTT broker hostname/IP | If MQTT enabled | |
| `MQTT_BROKER_PORT` | MQTT broker port | No | `1883` |
| `MQTT_SECURITY` | `none`, `username`, or `tls` | No | `none` |
| `MQTT_USERNAME` | MQTT username | No | |
| `MQTT_PASSWORD` | MQTT password | No | |
| `CALENDAR_ENABLED` | Enable ICS generation | No | `true` |
| `HOME_ASSISTANT_ENABLED` | Enable HA discovery | No | `true` |
| `CRON_SCHEDULE` | Cron schedule (Docker only) | No | `50 2 * * *` |
| `TZ` | Timezone | No | `Europe/London` |
| `ICS_PORT` | HTTP port for ICS files | No | `8080` |

### Config File

```bash
cp config/config.yaml.example config/config.yaml
```

```yaml
address:
  postcode: "TW3 3EB"
  address_hint: "7 Bath Rd"

mqtt:
  enabled: true
  broker_url: "your-mqtt-broker"
  broker_port: 1883
```

Environment variables override config file values.

### Address Matching

The address hint supports abbreviations and partial matches:

```
"132 Worple Rd"    -> matches "132, Worple Road, Isleworth, TW7 7HX"
"7 Bath Rd"        -> matches "7, Bath Road, Hounslow, TW3 3EB"
"Bath Road"        -> matches any address on Bath Road
```

To verify your exact address format, visit the [council website](https://my.hounslow.gov.uk/service/Waste_and_recycling_collections).

## Usage

### CLI

```bash
# Collect data only
hounslow-bins collect --postcode "TW3 3EB" --address-hint "7 Bath Rd"

# Collect and publish to MQTT
hounslow-bins mqtt --postcode "TW3 3EB" --address-hint "7 Bath Rd"

# Collect and generate calendar
hounslow-bins calendar --postcode "TW3 3EB" --address-hint "7 Bath Rd"

# Run all integrations
hounslow-bins all --postcode "TW3 3EB" --address-hint "7 Bath Rd"

# Show status
hounslow-bins status --postcode "TW3 3EB" --address-hint "7 Bath Rd"

# Serve ICS files over HTTP
hounslow-bins serve --port 8080
```

When using a config file, the `--postcode` and `--address-hint` flags are optional.

### Python API

```python
from hounslow_bin_collection.collector import HounslowBinCollector
from hounslow_bin_collection.models import AddressConfig

address = AddressConfig(postcode="TW3 3EB", address_hint="7 Bath Rd")
collector = HounslowBinCollector(headless=True)
data = collector.collect_bin_data(address)

for collection in data.collections:
    if collection.next_collection:
        print(f"{collection.type}: {collection.next_date_iso}")
# general_waste: 2026-04-14
# recycling: 2026-04-08
# food_waste: 2026-04-08
```

## MQTT Topics

All topics are published with `retain=True`.

### State Topics

| Topic | Description |
|-------|-------------|
| `hounslow_bins/bin_collection_general_waste/state` | Black Bin next date |
| `hounslow_bins/bin_collection_recycling/state` | Recycling next date |
| `hounslow_bins/bin_collection_food_waste/state` | Food Waste next date |
| `hounslow_bins/bin_collection_garden_waste/state` | Garden Waste next date |
| `hounslow_bins/next_waste_collection/state` | Consolidated: soonest collection with urgency |
| `hounslow_bins/bin_collection_status/state` | Online status, address, collection count |
| `hounslow_bins/diagnostics/last_run/state` | Timestamp of last collection run |
| `hounslow_bins/diagnostics/last_run_status/state` | success/error with detail |
| `hounslow_bins/diagnostics/page_accessible/state` | Council page reachability |
| `hounslow_bins/diagnostics/collection_count/state` | Number of waste types found |
| `hounslow_bins/diagnostics/sw_version/state` | Software version |
| `hounslow_bins/status` | Availability (`online`/`offline`) |

### Discovery Topics

Published to `homeassistant/sensor/<unique_id>/config` (and `binary_sensor`, `button`) for auto-discovery.

### Next Waste Collection Payload

The consolidated sensor provides attributes for dashboard cards:

```json
{
  "name": "Recycling",
  "date": "2026-04-08",
  "scheduled": "Wed 08 Apr",
  "icon": "mdi:recycle",
  "emoji": "\u267b\ufe0f",
  "icon_color": "blue",
  "waste_type": "recycling",
  "last_updated": "2026-04-01T20:41:18Z"
}
```

| Field | Values |
|-------|--------|
| `name` | "Black Bin", "Recycling", "Food Waste", "Garden Waste" |
| `scheduled` | "Today", "Tomorrow", "In 3 days", "Wed 08 Apr", etc. |
| `icon` | `mdi:trash-can`, `mdi:recycle`, `mdi:leaf`, `mdi:tree` |
| `icon_color` | `red` (today), `orange` (tomorrow), `amber` (3 days), or waste-type color |

## Home Assistant Integration

### Sensors

After MQTT publishing, these entities appear automatically under a single device:

| Entity ID | Type | Description |
|-----------|------|-------------|
| `sensor.hounslow_bins_bin_collection_general_waste` | sensor | Next Black Bin date |
| `sensor.hounslow_bins_bin_collection_recycling` | sensor | Next Recycling date |
| `sensor.hounslow_bins_bin_collection_food_waste` | sensor | Next Food Waste date |
| `sensor.hounslow_bins_bin_collection_garden_waste` | sensor | Next Garden Waste date |
| `sensor.hounslow_bins_next_waste_collection` | sensor | Soonest collection (for dashboard cards) |
| `sensor.hounslow_bins_last_run` | sensor | Last run timestamp |
| `sensor.hounslow_bins_last_run_status` | sensor | Last run result (success/error) |
| `binary_sensor.hounslow_bins_page_accessible` | binary_sensor | Council page reachable (problem if >24h) |
| `sensor.hounslow_bins_collection_count` | sensor | Waste types found |
| `sensor.hounslow_bins_sw_version` | sensor | Software version |
| `sensor.hounslow_bins_bin_collection_status` | sensor | Service status |
| `button.hounslow_bins_refresh` | button | Trigger immediate collection |

### Dashboard Card

A [Mushroom](https://github.com/piitaya/lovelace-mushroom) template card for the consolidated sensor is provided in [`ha_cards/`](ha_cards/). It shows the soonest collection with dynamic icon, color, and urgency badges.

### Calendar

The container serves ICS files over HTTP. Add the calendar to Home Assistant via the [Remote Calendar](https://www.home-assistant.io/integrations/remote_calendar/) integration:

1. **Settings > Devices & Services > Add Integration > Remote Calendar**
2. URL: `http://<container-host>:<ICS_PORT>/hounslow_bins.ics`
3. Name: "Waste Collection"

Calendar events use short names (Black Bin, Recycling, Food Waste) with evening and morning reminders.

## Docker Deployment

### Docker Compose

```bash
cp .env.example .env
# Edit .env with your address and MQTT details
docker-compose up -d
```

The container runs the collection on a cron schedule (default: 2:50 AM daily), serves ICS files on port 8208, and runs an initial collection on startup.

### Unraid

An Unraid community template is provided in [`unraid-template/`](unraid-template/).

### Container Image

```
ghcr.io/ronschaeffer/hounslow_bin_collection:latest
```

## Testing

```bash
make test              # Run pytest with coverage
make check             # Lint only (ruff)
make ci-check          # Lint + test (run before pushing)
```

## Development

```bash
poetry install --with dev
poetry run playwright install chromium
make install-hooks     # Install pre-commit hooks
make fix               # Auto-fix lint + format
make clean             # Remove caches
```

### Project Structure

```
src/hounslow_bin_collection/
  __main__.py            # CLI entry point (collect, mqtt, calendar, all, status, serve)
  config.py              # YAML + env var configuration
  models.py              # Data models (CollectionInfo, BinCollectionData, AddressConfig)
  collector.py           # High-level collection interface
  browser_collector.py   # Playwright automation
  enhanced_extractor.py  # Page content parsing
  integrations/
    mqtt.py              # MQTT publishing with HA discovery + diagnostics
    calendar.py          # ICS calendar generation
    web_server.py        # Lightweight HTTP server for ICS files
```

## License

[MIT](LICENSE)
