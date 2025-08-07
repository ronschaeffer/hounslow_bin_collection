# Hounslow Bin Collection - Home Assistant Cards

This directory contains a comprehensive set of Home Assistant dashboard cards for monitoring Hounslow bin collection schedules.

## Prerequisites

- Home Assistant with the Hounslow Bin Collection integration configured
- [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom) custom component installed
- [Browser Mod](https://github.com/thomasloven/hass-browser_mod) (optional, for popup functionality)

## Required Sensors

The cards expect sensors to be available in Home Assistant. There are two approaches:

### Option A: Individual Sensors (Default Cards)

- `binary_sensor.hounslow_bins_status` - System status sensor
- `sensor.hounslow_bins_general_waste` - General waste collection date
- `sensor.hounslow_bins_recycling` - Recycling collection date
- `sensor.hounslow_bins_food_waste` - Food waste collection date
- `sensor.hounslow_bins_garden_waste` - Garden waste collection date

### Option B: Unified Sensor (Alternative Approach)

- `sensor.next_waste_collection` - Combined sensor showing next collection with attributes:
  - `scheduled` - Human readable collection timing ("Today", "Tomorrow", "In 3 days")
  - `icon` - Dynamic icon based on collection type
  - `icon_color` - Dynamic color based on urgency
  - `next_collection_date` - ISO date of next collection
  - `days_until_next` - Number of days until collection

## Available Cards

### Core Cards (Individual Sensors)

### 1. Main Overview Card (`hounslow_bins_main_card.yaml`)

- **Purpose**: Primary dashboard card showing next collection and overall status
- **Features**:
  - Dynamic color coding based on collection urgency
  - Shows next collection type and date
  - System status indicator
  - Tap action for detailed view

### 2. Individual Bin Type Cards

- `hounslow_bins_general_waste_card.yaml` - General waste bin
- `hounslow_bins_recycling_card.yaml` - Recycling bin
- `hounslow_bins_food_waste_card.yaml` - Food waste bin
- `hounslow_bins_garden_waste_card.yaml` - Garden waste bin

**Features**:

- Individual collection dates and countdowns
- Color-coded urgency indicators
- Specific icons for each waste type
- "Put bin out" reminders

### 3. Status Card (`hounslow_bins_status_card.yaml`)

- **Purpose**: System health monitoring
- **Features**:
  - System operational status
  - Error indicators with badges
  - Last update timestamps
  - Visual alerts for system issues

### 4. Popup Card (`hounslow_bins_popup_card.yaml`)

- **Purpose**: Detailed collection information in a popup
- **Features**:
  - Full collection schedule
  - System status details
  - Compact overview cards
- **Requirements**: Browser Mod component

### 5. Summary Card (`hounslow_bins_summary_card.yaml`)

- **Purpose**: Comprehensive markdown summary
- **Features**:
  - Detailed collection information
  - Collection rules and guidelines
  - Quick action links
  - System status overview

### Unified Sensor Cards (Alternative Approach)

### 6. Unified Sensor Card (`hounslow_unified_sensor_card.yaml`)

- **Purpose**: Simple card for existing unified sensor setups
- **Features**:
  - Uses `sensor.next_waste_collection` with attributes
  - Displays dynamic icon and color from sensor
  - Shows scheduled timing from sensor
  - Badge alerts for urgent collections

### 7. Advanced Unified Card (`hounslow_advanced_unified_card.yaml`)

- **Purpose**: Enhanced card with additional logic and fallbacks
- **Features**:
  - Smart icon detection based on collection type
  - Fallback color logic when sensor doesn't provide colors
  - Handles multiple collection display ("Rec + Garden")
  - Enhanced urgency detection

## Color Coding System

The cards use a consistent color scheme to indicate collection urgency:

- 🔴 **Red**: Collection today - immediate action required
- 🟠 **Orange**: Collection tomorrow - put bin out tonight
- 🟡 **Yellow**: Collection in 2-3 days - prepare bin
- 🟢 **Green**: Collection more than 3 days away
- 🔵 **Blue**: Recycling collections (when not urgent)
- 🟤 **Brown**: Food waste specific
- ⚫ **Grey**: Unknown status or completed collections

## Installation Instructions

### Option 1: Individual Cards (Default Approach)

1. Copy the desired card YAML content
2. In Home Assistant, go to your dashboard
3. Add a new card and select "Manual" card type
4. Paste the YAML content
5. Save the card

### Option 2: Unified Sensor Card (For Existing Unified Sensors)

If you already have a `sensor.next_waste_collection` with attributes:

```yaml
# Simple unified card
- !include ha_cards/hounslow_unified_sensor_card.yaml

# Or advanced unified card with fallback logic
- !include ha_cards/hounslow_advanced_unified_card.yaml
```

### Option 3: Complete Setup (Individual Sensors)

For a complete bin collection dashboard section:

```yaml
type: vertical-stack
title: "Bin Collections"
cards:
  # Main overview card
  - !include ha_cards/hounslow_bins_main_card.yaml

  # Individual bin cards in a grid
  - type: grid
    columns: 2
    square: false
    cards:
      - !include ha_cards/hounslow_bins_general_waste_card.yaml
      - !include ha_cards/hounslow_bins_recycling_card.yaml
      - !include ha_cards/hounslow_bins_food_waste_card.yaml
      - !include ha_cards/hounslow_bins_garden_waste_card.yaml

  # Status and info cards
  - type: horizontal-stack
    cards:
      - !include ha_cards/hounslow_bins_status_card.yaml
      - !include ha_cards/hounslow_bins_popup_card.yaml
```

### Option 4: Create Unified Sensor from Individual Sensors

If you have individual sensors but want a unified sensor, add the template from `unified_sensor_template.yaml` to your `configuration.yaml`:

```yaml
# Copy contents of unified_sensor_template.yaml to your configuration.yaml
# This creates sensor.next_waste_collection from individual sensors
```

### Option 5: Markdown Summary Only

For a simple text-based overview:

```yaml
- !include ha_cards/hounslow_bins_summary_card.yaml
```

## Customization

### Changing Icons

Modify the `icon:` property in each card. Available icons from [Material Design Icons](https://materialdesignicons.com/):

- `mdi:trash-can` (general waste)
- `mdi:recycle` (recycling)
- `mdi:food-apple` (food waste)
- `mdi:flower` (garden waste)

### Adjusting Colors

Modify the `icon_color:` sections in each card. Available colors:

- Standard: `red`, `orange`, `yellow`, `green`, `blue`, `brown`, `grey`
- Extended: `purple`, `pink`, `cyan`, `lime`, `indigo`

### Collection Time Customization

The cards respect collection timing configured in your main application. The default behavior assumes:

- Collections occur between 06:00-18:00
- Bins should be out by 06:00 on collection day
- Evening before reminders for next-day collections

## Troubleshooting

### Cards Not Showing Data

1. Verify sensors are available: `Developer Tools > States`
2. Check sensor names match exactly (case-sensitive)
3. Ensure Hounslow Bin Collection integration is running

### Popup Not Working

1. Install Browser Mod component
2. Configure Browser Mod in Home Assistant
3. Check browser console for JavaScript errors

### Colors Not Displaying

1. Verify Mushroom Cards are installed and up-to-date
2. Check for any theme conflicts
3. Test with Home Assistant default theme

### Template Errors

1. Check Home Assistant logs for template errors
2. Verify date format matches sensor output (`YYYY-MM-DD`)
3. Test templates in `Developer Tools > Template`

## Integration with Automations

These cards can be enhanced with Home Assistant automations:

### Collection Day Notifications

```yaml
automation:
  - alias: "Bin Collection Reminder"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: template
        value_template: |
          {% set tomorrow = (now() + timedelta(days=1)).strftime('%Y-%m-%d') %}
          {{ states('sensor.hounslow_bins_general_waste') == tomorrow or
             states('sensor.hounslow_bins_recycling') == tomorrow or
             states('sensor.hounslow_bins_food_waste') == tomorrow or
             states('sensor.hounslow_bins_garden_waste') == tomorrow }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Remember to put bins out for collection tomorrow!"
```

### Status Monitoring

```yaml
automation:
  - alias: "Bin Collection System Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.hounslow_bins_status
        to: "off"
    action:
      - service: notify.home_assistant
        data:
          message: "Hounslow Bin Collection system error detected!"
```

## Support

For issues with the cards:

1. Check Home Assistant logs
2. Verify all prerequisites are installed
3. Test individual sensors in Developer Tools
4. Check template syntax in Template editor

For issues with the underlying data:

1. Check Hounslow Bin Collection integration logs
2. Verify configuration settings
3. Test manual collection data fetch
