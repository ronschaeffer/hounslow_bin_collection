#!/usr/bin/env python3
# waste_sync.py

import requests
import json
import time
import sys
import os
from datetime import datetime
from ics import Calendar, Event
import paho.mqtt.client as mqtt

_URL = "https://my.hounslow.gov.uk/api/custom-widgets/getRoundDates"

class WasteCollection:
    def __init__(self, uprn: str):
        if not uprn or not uprn.isdigit(): 
            raise ValueError("A valid numeric UPRN must be provided.")
        self._uprn = uprn
        
    def fetch_data(self) -> dict:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        payload = {"uprn": self._uprn}
        
        try:
            response = requests.post(_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            api_response = response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            raise RuntimeError(f"Could not get data for UPRN {self._uprn}: {e}") from e
            
        if not api_response.get("success"): 
            raise RuntimeError(f"API returned failure for UPRN {self._uprn}")
            
        structured_collections = {}
        for round_item in api_response.get("data", {}).get("rounds", []):
            bin_type = round_item.get("roundType").title()
            next_coll = round_item.get("nextCollection")
            foll_coll = round_item.get("followingCollection")
            
            structured_collections[bin_type] = {
                'next': datetime.fromisoformat(next_coll).date() if next_coll else None,
                'following': datetime.fromisoformat(foll_coll).date() if foll_coll else None
            }
        return structured_collections

def get_icon_for_bin(bin_type):
    if "refuse" in bin_type.lower(): 
        return "mdi:trash-can"
    if "recycling" in bin_type.lower(): 
        return "mdi:recycle"
    if "garden" in bin_type.lower(): 
        return "mdi:flower"
    if "food" in bin_type.lower(): 
        return "mdi:food-apple-outline"
    return "mdi:delete-empty"

if __name__ == "__main__":
    uprn = os.getenv('UPRN')
    ics_path = os.getenv('ICS_FILE_PATH', '/app/www/waste_calendar.ics')
    mqtt_enabled = os.getenv('MQTT_ENABLED', 'true').lower() in ('true', '1', 't')
    mqtt_config = {
        "broker": os.getenv('MQTT_BROKER'),
        "port": int(os.getenv('MQTT_PORT', 1883)),
        "username": os.getenv('MQTT_USERNAME'),
        "password": os.getenv('MQTT_PASSWORD'),
        "discovery_prefix": os.getenv('DISCOVERY_PREFIX', 'homeassistant')
    }

    if not uprn: 
        print("Error: UPRN environment variable is required.")
        sys.exit(1)

    print(f"[{datetime.now()}] Starting Hounslow Bin Collection Calendar sync for UPRN {uprn}...")
    
    status = "OK"
    error_message = None
    exit_code = 0
    client = None
    
    if mqtt_enabled:
        if not mqtt_config['broker']: 
            print("Error: MQTT_BROKER is required when MQTT is enabled.")
            sys.exit(1)
        client = mqtt.Client()
        if mqtt_config.get('username'): 
            client.username_pw_set(mqtt_config['username'], mqtt_config.get('password'))
        try: 
            client.connect(mqtt_config.get('broker'), mqtt_config.get('port'), 60)
            client.loop_start()
        except Exception as e: 
            print(f"Could not connect to MQTT broker: {e}")
            client = None

    try:
        collections = WasteCollection(uprn=uprn).fetch_data()
        today = datetime.now().date()
        device_info = {
            "identifiers": [f"hounslow_waste_{uprn}"],
            "name": "Hounslow Waste Collection",
            "manufacturer": "Hounslow Council API"
        }
        
        if client:
            print("MQTT is enabled. Publishing sensor data...")
            for bin_type, dates in collections.items():
                if not dates.get('next'): 
                    continue
                object_id = bin_type.lower().replace(" ", "_")
                base_topic = f"{mqtt_config.get('discovery_prefix')}/sensor/hounslow-bin-collection-calendar/{object_id}"
                
                config_payload = {
                    "name": f"Hounslow {bin_type}",
                    "unique_id": f"hounslow_waste_{uprn}_{object_id}",
                    "device_class": "date",
                    "state_topic": f"{base_topic}/state",
                    "json_attributes_topic": f"{base_topic}/attributes",
                    "device": device_info,
                    "icon": get_icon_for_bin(bin_type)
                }
                
                attributes_payload = {
                    "days_until_collection": (dates['next'] - today).days,
                    "following_collection": dates['following'].isoformat() if dates['following'] else "None",
                    "last_update": datetime.now().isoformat()
                }
                
                client.publish(f"{base_topic}/config", json.dumps(config_payload), retain=True)
                client.publish(f"{base_topic}/state", dates['next'].isoformat())
                client.publish(f"{base_topic}/attributes", json.dumps(attributes_payload))
            print("MQTT sensor data published.")
            
        print("Generating ICS calendar file...")
        # Ensure directory exists
        os.makedirs(os.path.dirname(ics_path), exist_ok=True)
        
        c = Calendar()
        for bin_type, dates in collections.items():
            for collection_type in ['next', 'following']:
                if dates.get(collection_type):
                    e = Event()
                    e.name = f"{bin_type} Collection"
                    e.begin = dates[collection_type]
                    e.make_all_day()
                    c.events.add(e)
        
        with open(ics_path, 'w') as f: 
            f.write(str(c))
        print(f"Successfully generated ICS file at: {ics_path}")

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        status = "Error"
        error_message = str(e)
        exit_code = 1

    finally:
        if client:
            print("Publishing final status sensor...")
            status_base_topic = f"{mqtt_config.get('discovery_prefix')}/sensor/hounslow-bin-collection-calendar/status"
            status_config = {
                "name": "Hounslow Bin Collection Status",
                "unique_id": f"hounslow_waste_{uprn}_status",
                "state_topic": f"{status_base_topic}/state",
                "json_attributes_topic": f"{status_base_topic}/attributes",
                "device": device_info,
                "icon_template": "{% if value == 'OK' %}mdi:sync{% else %}mdi:sync-alert{% endif %}"
            }
            status_attributes = {
                "last_run": datetime.now().isoformat(),
                "last_error": error_message,
                "uprn": uprn
            }
            client.publish(f"{status_base_topic}/config", json.dumps(status_config), retain=True)
            client.publish(f"{status_base_topic}/state", status)
            client.publish(f"{status_base_topic}/attributes", json.dumps(status_attributes))
            time.sleep(1)
            client.loop_stop()
            client.disconnect()
            print("MQTT status publishing complete.")
            
    print(f"[{datetime.now()}] Script finished with status: {status}")
    sys.exit(exit_code)
