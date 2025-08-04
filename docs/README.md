# Hounslow Bin Collection Calendar Documentation

This directory contains documentation for the Hounslow Bin Collection Calendar project.

## Project Overview

This project fetches waste collection data from the London Borough of Hounslow Council API and integrates it with Home Assistant using MQTT sensors and iCalendar files. It's designed to run as a Docker container with scheduled data synchronization.

## Documentation Structure

- `examples.md` - Usage examples and integration guides
- `README.md` - This documentation index

## Key Features

- **MQTT Auto-Discovery**: Automatically creates Home Assistant sensors for waste collection dates
- **iCalendar Integration**: Generates `.ics` files for calendar applications
- **Docker Deployment**: Containerized with built-in scheduler and web server
- **Hounslow Council API**: Direct integration with official waste collection data

## Quick Start

See the main [README.md](../README.md) in the project root for installation instructions.

For usage examples and integration patterns, see [examples.md](examples.md).

## Development Setup

```bash
# Clone and setup
git clone https://github.com/ronschaeffer/hounslow_bin_collection.git
cd hounslow_bin_collection

# Install with Poetry
poetry install
poetry shell

# Set required environment variables
export UPRN=your_uprn_here
export MQTT_ENABLED=false

# Run the sync script
python waste_sync.py
```
