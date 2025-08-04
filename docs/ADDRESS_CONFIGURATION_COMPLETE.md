# 🏠 Address Configuration & Environment Variables - Complete Implementation

## ✅ **IMPLEMENTED: Smart Address Configuration System**

The Hounslow Bin Collection system now supports flexible address configuration through **environment variables**, **configuration files**, and **enhanced address matching**.

## 🎯 **Address Configuration Methods**

### **Method 1: Environment Variables (Recommended for Docker/Production)**

```bash
# Option A: Browser automation with enhanced matching
export HOUNSLOW_POSTCODE="TW3 3EB"
export HOUNSLOW_ADDRESS="7 Bath Rd"

# Option B: Direct UPRN (fastest, most reliable)
export UPRN="100021577775"
```

### **Method 2: Configuration File**

```yaml
# config/config.yaml
address:
  postcode: "TW3 3EB"
  address_hint: "7 Bath Rd"
  uprn: null # Set this to override postcode/address
```

### **Method 3: Direct Code Usage**

```python
from hounslow_bin_collection.browser_collector import BrowserWasteCollector

with BrowserWasteCollector() as collector:
    result = collector.fetch_collection_data("TW3 3EB", "7 Bath Rd")
```

## 🚀 **Enhanced Address Matching**

The system automatically handles common address variations:

✅ **Smart Abbreviation Expansion:**

- `Rd` → `Road`, `St` → `Street`, `Ave` → `Avenue`
- `Ln` → `Lane`, `Cl` → `Close`, `Cres` → `Crescent`
- `Dr` → `Drive`, `Pk` → `Park`, `Pl` → `Place`

✅ **Flexible Input Formats:**

- `"7 Bath Rd"` → Matches `"7 Bath Road, Hounslow"`
- `"136 Worple Rd"` → Matches `"136 Worple Road, Isleworth"`
- `"Bath Road"` → Matches any address on Bath Road
- `"7"` → Matches house number 7
- `"Library"` → Matches building names

## 🐳 **Docker & Production Usage**

### **Docker Compose**

```yaml
services:
  hounslow-bin-collection:
    image: hounslow-bin-collection
    environment:
      - HOUNSLOW_POSTCODE=TW3 3EB
      - HOUNSLOW_ADDRESS=7 Bath Rd
      - MQTT_BROKER=192.168.1.100
      - MQTT_ENABLED=true
```

### **Environment File (.env)**

```bash
# Address configuration
HOUNSLOW_POSTCODE=TW3 3EB
HOUNSLOW_ADDRESS=7 Bath Rd

# OR use UPRN directly
# UPRN=100021577775

# MQTT configuration
MQTT_BROKER=192.168.1.100
MQTT_ENABLED=true
```

## 🏡 **Home Assistant Integration**

### **Automatic Sensor Discovery**

When `MQTT_ENABLED=true`, sensors appear automatically:

- `sensor.hounslow_refuse`
- `sensor.hounslow_recycling`
- `sensor.hounslow_food_waste`
- `sensor.hounslow_garden_waste`
- `sensor.hounslow_bin_collection_status`

### **iCalendar Integration**

Access your calendar at: `http://YOUR_SERVER_IP:8208/waste_calendar.ics`

## 📋 **Configuration Variables Reference**

| Variable            | Description                        | Required | Example         |
| ------------------- | ---------------------------------- | -------- | --------------- |
| `HOUNSLOW_POSTCODE` | Your postcode for address lookup   | Yes\*    | `TW3 3EB`       |
| `HOUNSLOW_ADDRESS`  | Address hint for enhanced matching | Yes\*    | `7 Bath Rd`     |
| `UPRN`              | Direct UPRN (overrides postcode)   | Yes\*    | `100021577775`  |
| `MQTT_ENABLED`      | Enable MQTT sensors                | No       | `true`          |
| `MQTT_BROKER`       | MQTT broker IP/hostname            | No\*\*   | `192.168.1.100` |
| `CRON_SCHEDULE`     | Collection sync schedule           | No       | `50 2 * * *`    |
| `ICS_PORT`          | Calendar web server port           | No       | `8208`          |

\*One method required: Either `UPRN` OR (`HOUNSLOW_POSTCODE` + `HOUNSLOW_ADDRESS`)
\*\*Required if `MQTT_ENABLED=true`

## 🧪 **Testing & Validation**

### **Test Environment Variable Configuration**

```bash
poetry run python test_env_config.py
```

### **Test Enhanced Address Matching**

```bash
poetry run python demo_env_vars.py
```

### **Test Address Matching Flexibility**

```bash
poetry run python test_address_matching.py
```

## 🔗 **Manual Address Verification**

For 100% accuracy, verify your exact address at:
**https://my.hounslow.gov.uk/service/Waste_and_recycling_collections**

1. Enter your postcode
2. Select your address from dropdown
3. Copy the exact text for configuration

## 💡 **Best Practices**

### **For Development:**

```bash
# Use environment variables
export HOUNSLOW_POSTCODE="TW3 3EB"
export HOUNSLOW_ADDRESS="7 Bath Rd"
export MQTT_ENABLED="false"

poetry run python waste_sync.py
```

### **For Production (Docker):**

```bash
# Use .env file or docker environment
docker run -e HOUNSLOW_POSTCODE="your_postcode" \
           -e HOUNSLOW_ADDRESS="your_address" \
           -e MQTT_BROKER="192.168.1.100" \
           hounslow-bin-collection
```

### **For Home Assistant:**

```yaml
# docker-compose.yml
environment:
  - HOUNSLOW_POSTCODE=your_postcode
  - HOUNSLOW_ADDRESS=your_address
  - MQTT_BROKER=192.168.1.100
  - MQTT_ENABLED=true
```

## 🎯 **Key Benefits**

1. **Flexible Configuration**: Environment variables, config files, or direct code
2. **Smart Address Matching**: Handles abbreviations and partial addresses automatically
3. **Production Ready**: Environment variable support for Docker deployments
4. **Home Assistant Ready**: Automatic MQTT sensor discovery
5. **Manual Fallback**: Clear guidance for manual address verification
6. **Backwards Compatible**: Existing code continues to work unchanged

---

**✅ COMPLETE: Smart address configuration with environment variables, enhanced matching, and production-ready deployment options successfully implemented!**
