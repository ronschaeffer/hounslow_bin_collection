# Hounslow Bin Collection Calendar

[![License: MIT](https://img.shields.io/github/license/ronschaeffer/hounslow-bin-collection-calendar)](https://opensource.org/licenses/MIT)
[![GitHub Container Registry](https://img.shields.io/badge/GHCR-ghcr.io/ronschaeffer/hounslow--bin--collection--calendar-blue?logo=github)](https://github.com/ronschaeffer/hounslow-bin-collection-calendar/pkgs/container/hounslow-bin-collection-calendar)

This project provides automated browser-based extraction of waste collection data for properties in the London Borough of Hounslow. It uses sophisticated browser automation to bypass API security measures and extract real-time collection schedules directly from the official council website.

The project is designed to be deployed as a Docker container, with all configuration handled by environment variables for maximum portability and security.

---

## How It Works

The container runs browser automation that:

1. **Navigates to** Hounslow Council's official waste collection form
2. **Enters your postcode** and selects your specific address
3. **Extracts collection data** including bin types, frequencies, and specific dates
4. **Publishes to MQTT** (optional) for Home Assistant integration
5. **Generates iCalendar** files for calendar applications

**Important:** Collection dates may vary due to holidays and service changes. This tool extracts real-time data directly from the council's system to ensure accuracy.

## Features

- **Browser Automation:** Uses Playwright to navigate the official council website
- **Real-time Data:** Extracts current collection schedules including holiday adjustments
- **Configurable Address:** Use any valid Hounslow postcode and address
- **MQTT Auto-Discovery:** Automatically creates Home Assistant sensors for each waste type
- **Self-Hosted iCalendar:** Built-in web server provides stable local URLs for calendar files
- **Status Monitoring:** Dedicated health-check sensors for monitoring
- **Fully Containerized:** Lightweight Docker image with built-in scheduler
- **Production Ready:** Headless browser operation suitable for server deployment

## Quick Start

### Testing with Hounslow Council's Address

For testing and demonstration, the tool uses Hounslow Council's own address by default:

```bash
# Test with default address (Hounslow Council HQ)
poetry run python demo_final.py

# Or get JSON output
poetry run python demo_final.py --json
```

This will demonstrate the tool using:
- **Postcode:** TW3 3EB
- **Address:** 7 Bath Rd, Hounslow
- **(Hounslow Council headquarters)**

### Configuration for Your Address

Copy the example configuration and customize for your address:

## Installation (Docker Recommended)

### On Unraid (Easiest Method)

1.  **Install:** In the Unraid UI, go to the **Apps** tab and search for `HounslowBinCollectionCalendar`. Click **Install**.
2.  **Configure:** Fill in the template fields with your details. You must provide your `UPRN`. If using MQTT, also provide your `MQTT_BROKER`.
3.  **Deploy & Start:** Click Apply to start the container.

### On any other Docker host (via Docker Compose)

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/ronschaeffer/hounslow-bin-collection-calendar.git
    cd hounslow-bin-collection-calendar
    ```
2.  **Create Configuration File:** Copy the example `.env` file.
    ```bash
    cp .env.example .env
    ```
3.  **Edit Configuration:** Open the `.env` file with a text editor and fill in your UPRN, MQTT details, and any other settings you wish to customize.
4.  **Run:** Use Docker Compose to build and start the container in the background.
    ```bash
    docker-compose up --build -d
    ```

## Home Assistant Integration

### 1. MQTT Sensors

If `MQTT_ENABLED` is `true`, the following sensors will appear automatically in Home Assistant:

- **Collection Sensors:** `sensor.hounslow_refuse`, `sensor.hounslow_recycling`, etc.
- **Status Sensor:** `sensor.hounslow_bin_collection_status`. The state is `OK` or `Error`. Check its attributes for the last run time and any error messages.

### 2. iCalendar

The script generates an `.ics` file and serves it locally.

1.  **Find Your URL:** The URL for your calendar is `http://<YOUR_DOCKER_HOST_IP>:<ICS_PORT>/waste_calendar.ics`.
    - `<YOUR_DOCKER_HOST_IP>` is the IP address of your Unraid server or Docker machine.
    - `<ICS_PORT>` is the port you configured (default: `8208`).
    - _Example:_ `http://192.168.1.50:8208/waste_calendar.ics`
2.  **Add to Home Assistant:** Go to **Settings > Devices & Services > Add Integration** and find **iCalendar Platform**.
3.  Paste the URL from Step 1 into the URL field and give your calendar a name.

## Configuration Variables

| Variable        | Description                                                                | Required                    | Default Value |
| --------------- | -------------------------------------------------------------------------- | --------------------------- | ------------- |
| `UPRN`          | Your Unique Property Reference Number.                                     | **Yes**                     | `None`        |
| `CRON_SCHEDULE` | The `cron` schedule for running the sync.                                  | No                          | `50 2 * * *`  |
| `TZ`            | Your local timezone (e.g., `Europe/London`).                               | No                          | `None`        |
| `ICS_PORT`      | The **host port** for the built-in web server that serves the `.ics` file. | No                          | `8208`        |
| `MQTT_ENABLED`  | Set to `true` to enable creating Home Assistant sensors via MQTT.          | No                          | `true`        |
| `MQTT_BROKER`   | IP address or hostname of your MQTT broker.                                | **If MQTT_ENABLED is true** | `None`        |
| `MQTT_PORT`     | The port for your MQTT broker.                                             | No                          | `1883`        |
| `MQTT_USERNAME` | Your MQTT username.                                                        | No                          | `None`        |
| `MQTT_PASSWORD` | Your MQTT password.                                                        | No                          | `None`        |

## Development

This project can also be run locally for development:

1. **Setup Environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .[dev]
   ```

2. **Run the script:**

   ```bash
   # Set required environment variables
   export UPRN=your_uprn_here
   export MQTT_ENABLED=false  # or configure MQTT settings

   # Run the script
   python waste_sync.py
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
