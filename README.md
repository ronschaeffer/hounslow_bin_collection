# Hounslow Bin Collection

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Automated waste collection schedule scraper for the London Borough of Hounslow. Uses browser automation to extract real-time bin collection dates from the council website, publishes to MQTT for Home Assistant, and generates ICS calendar files.

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [MQTT Topics](#mqtt-topics)
7. [Home Assistant Integration](#home-assistant-integration)
8. [Docker Deployment](#docker-deployment)
9. [Testing](#testing)
10. [Development](#development)
11. [License](#license)

---

## Features

- **Browser Automation:** Playwright-based scraping of the official Hounslow Council website
- **Smart Address Matching:** Abbreviation expansion (`Rd` to `Road`, `St` to `Street`, etc.) and fuzzy matching
- **MQTT Auto-Discovery:** Creates Home Assistant sensors for each waste type via retained discovery topics
- **Consolidated Sensor:** Single `next_waste_collection` sensor showing the soonest collection with urgency attributes
- **ICS Calendar:** Generates calendar files with evening and morning reminders
- **Fully Containerized:** Docker image with built-in cron scheduler

## How It Works

1. Navigates to Hounslow Council's waste collection form
2. Enters your postcode, selects your address from the dropdown
3. Extracts collection types, frequencies, and next/last dates
4. Publishes to MQTT (Home Assistant discovery) and/or generates ICS calendar

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
| `MQTT_USERNAME` | MQTT username | No | |
| `MQTT_PASSWORD` | MQTT password | No | |
| `CALENDAR_ENABLED` | Enable ICS generation | No | `true` |
| `HOME_ASSISTANT_ENABLED` | Enable HA discovery | No | `true` |

### Config File

Copy the example and edit:

```bash
cp config/config.yaml.example config/config.yaml
```

```yaml
address:
  postcode: "TW7 7HX"
  address_hint: "132 Worple Rd"

mqtt:
  enabled: true
  broker_url: "10.10.10.20"
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
poetry run hounslow-bins collect

# Collect and publish to MQTT
poetry run hounslow-bins mqtt

# Collect and generate calendar
poetry run hounslow-bins calendar

# Run all integrations
poetry run hounslow-bins all

# Show status
poetry run hounslow-bins status
```

### Python API

```python
from hounslow_bin_collection.collector import HounslowBinCollector
from hounslow_bin_collection.models import AddressConfig

address = AddressConfig(postcode="TW7 7HX", address_hint="132 Worple Rd")
collector = HounslowBinCollector(headless=True)
data = collector.collect_bin_data(address)

for collection in data.collections:
    if collection.next_collection:
        print(f"{collection.type}: {collection.next_date_iso}")
```

## MQTT Topics

All topics are published with `retain=True`.

### State Topics

| Topic | Description |
|-------|-------------|
| `hounslow_bins/bin_collection_general_waste/state` | General waste next date and metadata |
| `hounslow_bins/bin_collection_recycling/state` | Recycling next date and metadata |
| `hounslow_bins/bin_collection_food_waste/state` | Food waste next date and metadata |
| `hounslow_bins/bin_collection_garden_waste/state` | Garden waste next date and metadata |
| `hounslow_bins/next_waste_collection/state` | Consolidated: soonest collection with urgency |
| `hounslow_bins/bin_collection_status/state` | Online status, address, collection count |
| `hounslow_bins/status` | Availability (`online`/`offline`) |

### Discovery Topics

Published to `homeassistant/sensor/<unique_id>/config` for auto-discovery.

### Next Waste Collection Payload

The consolidated sensor provides attributes for dashboard cards:

```json
{
  "name": "Recycling Collection",
  "date": "2026-04-08",
  "scheduled": "Wed 08 Apr",
  "icon": "mdi:recycle",
  "icon_color": "blue",
  "waste_type": "recycling",
  "last_updated": "2026-04-01T20:41:18.917067"
}
```

The `scheduled` field provides human-readable text: "Today", "Tomorrow", "In 3 days", "Wed 08 Apr", etc.
The `icon_color` reflects urgency: `red` (today), `orange` (tomorrow), `amber` (within 3 days), or waste-type color.

## Home Assistant Integration

### Sensors

After MQTT publishing, these sensors appear automatically:

| Entity ID | Description |
|-----------|-------------|
| `sensor.hounslow_bins_bin_collection_general_waste` | Next general waste date |
| `sensor.hounslow_bins_bin_collection_recycling` | Next recycling date |
| `sensor.hounslow_bins_bin_collection_food_waste` | Next food waste date |
| `sensor.hounslow_bins_bin_collection_garden_waste` | Next garden waste date |
| `sensor.hounslow_bins_next_waste_collection` | Soonest collection (for cards) |
| `sensor.hounslow_bins_bin_collection_status` | Service status |

### Dashboard Card

A Mushroom template card for the consolidated sensor is provided in [`ha_cards/`](ha_cards/).

### iCalendar

The generated `.ics` file can be added to Home Assistant via **Settings > Devices & Services > Add Integration > iCalendar**.

## Docker Deployment

### Docker Compose

```bash
cp .env.example .env
# Edit .env with your address and MQTT details
docker-compose up -d
```

### Unraid

An Unraid community template is provided in [`unraid-template/`](unraid-template/).

## Testing

```bash
make test              # Run pytest with coverage
make check             # Lint only (ruff)
make ci-check          # Lint + test (run before pushing)
```

## Development

```bash
poetry install --with dev
make install-hooks     # Install pre-commit hooks
make fix               # Auto-fix lint + format
make clean             # Remove caches
```

### Project Structure

```
src/hounslow_bin_collection/
  __main__.py            # CLI entry point
  config.py              # YAML + env var configuration
  models.py              # Data models (CollectionInfo, BinCollectionData)
  collector.py           # High-level collection interface
  browser_collector.py   # Playwright automation
  enhanced_extractor.py  # Page content parsing
  integrations/
    mqtt.py              # MQTT publishing with HA discovery
    calendar.py          # ICS calendar generation
```

## License

[MIT](LICENSE)
