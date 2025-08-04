# Hounslow Bin Collection Examples

This document contains usage examples for the Hounslow Bin Collection Calendar system.

## Python API Usage

### Basic Waste Collection Data Fetching

```python
from waste_sync import WasteCollection

# Initialize with your UPRN (Unique Property Reference Number)
waste_collector = WasteCollection(uprn="your_uprn_here")

# Fetch collection data from Hounslow Council API
data = waste_collector.fetch_data()
print(f"Next collections: {data}")
```

### Configuration Management

```python
from hounslow_bin_collection.config import Config

# Load configuration from file
config = Config()

# Get configuration values with defaults
uprn = config.get('uprn')
mqtt_broker = config.get('mqtt.broker', 'localhost')
mqtt_port = config.get('mqtt.port', 1883)
cron_schedule = config.get('cron_schedule', '50 2 * * *')

# Set configuration values
config.set('mqtt.enabled', True)
config.set('mqtt.broker', '192.168.1.100')
config.save()
```

### MQTT Integration Example

```python
import paho.mqtt.client as mqtt
from waste_sync import WasteCollection

# Setup MQTT client
client = mqtt.Client()
client.connect("your_mqtt_broker", 1883, 60)

# Fetch and publish waste collection data
waste_collector = WasteCollection("your_uprn")
data = waste_collector.fetch_data()

# Publish to Home Assistant via MQTT auto-discovery
for collection_type, date in data.items():
    topic = f"homeassistant/sensor/hounslow_{collection_type}/config"
    payload = {
        "name": f"Hounslow {collection_type.title()}",
        "state_topic": f"hounslow/waste/{collection_type}",
        "device_class": "timestamp",
        "unique_id": f"hounslow_{collection_type}"
    }
    client.publish(topic, json.dumps(payload))
    client.publish(f"hounslow/waste/{collection_type}", date)
```

### iCalendar Generation

```python
from ics import Calendar, Event
from datetime import datetime
from waste_sync import WasteCollection

# Fetch waste collection data
waste_collector = WasteCollection("your_uprn")
data = waste_collector.fetch_data()

# Create iCalendar
calendar = Calendar()

# Add events for each collection type
for collection_type, date_str in data.items():
    event = Event()
    event.name = f"{collection_type.title()} Collection"
    event.begin = datetime.fromisoformat(date_str)
    event.description = f"Hounslow {collection_type} waste collection"
    calendar.events.add(event)

# Save calendar file
with open('waste_calendar.ics', 'w') as f:
    f.writelines(calendar.serialize_iter())
```

## Environment Configuration

### Docker Environment Variables

```bash
# Required
UPRN=your_property_uprn

# MQTT Configuration (optional)
MQTT_ENABLED=true
MQTT_BROKER=192.168.1.100
MQTT_PORT=1883
MQTT_USERNAME=homeassistant
MQTT_PASSWORD=your_password

# Scheduling
CRON_SCHEDULE="50 2 * * *"  # Daily at 2:50 AM
TZ=Europe/London

# Web server for iCalendar
ICS_PORT=8208
```

### Local Development

```bash
# Set up environment
export UPRN=your_uprn_here
export MQTT_ENABLED=false
export TZ=Europe/London

# Run the sync script
python waste_sync.py
```

## Home Assistant Integration

### MQTT Sensors

After running with MQTT enabled, these sensors will appear:

```yaml
# Example sensor entities created automatically
sensor.hounslow_refuse:
  state: "2025-08-15T00:00:00"
  attributes:
    friendly_name: "Hounslow Refuse"
    device_class: "timestamp"

sensor.hounslow_recycling:
  state: "2025-08-22T00:00:00"
  attributes:
    friendly_name: "Hounslow Recycling"
    device_class: "timestamp"
```

### iCalendar Integration

```yaml
# configuration.yaml
calendar:
  - platform: ical
    url: "http://192.168.1.100:8208/waste_calendar.ics"
    name: "Hounslow Waste Collection"
```
