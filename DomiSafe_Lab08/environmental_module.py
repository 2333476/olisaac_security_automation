


import json
import time
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os

import board

import adafruit_dht
# Initialize the DHT device, with data pin connected to:
dhtDevice = adafruit_dht.DHT11(board.D4, use_pulseio=False)
# For DHT22:  dhtDevice = adafruit_dht.DHT22(board.D4)  # or board.D18, etc.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class environmental_module:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        default_config = {
            "ADAFRUIT_IO_USERNAME": "username",
            "ADAFRUIT_IO_KEY": "userkey",
            "MQTT_BROKER": "io.adafruit.com",
            "MQTT_PORT": 1883,
            "MQTT_KEEPALIVE": 60,
            "devices": ["living_room_light", "bedroom_fan", "front_door", "garage_door"],
            "camera_enabled": True,
            "capturing_interval": 900,
            "flushing_interval": 10,
            "sync_interval": 300
        }

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return default_config



    def get_environmental_data(self):
        temperature_c, humidity, pressure = 0, 0, 0
        try:
            # Simulate realistic temperature variations
            base_temp = 22 + 5 * math.sin(time.time() / 3600)  # Daily cycle
            temperature_c = round(base_temp + random.uniform(-2, 2), 1)

            # Humidity inversely related to temperature
            humidity = round(60 - (temperature_c - 20) * 2 + random.uniform(-5, 5), 1)
            humidity = max(30, min(90, humidity))  # Clamp between 30-90%

            # Pressure with small variations
            pressure = round(1013.25 + random.uniform(-10, 10), 2)

            # Read temperature and humidity
            #temperature_c = dhtDevice.temperature
            #temperature_f = temperature_c * (9 / 5) + 32
            #humidity = dhtDevice.humidity

            #print(f"Temp: {temperature_c:.1f} C ({temperature_f:.1f} F)")
            #print(f"Humidity: {humidity:.1f}%")

        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
            time.sleep(2.0)

        return {
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature_c,
            'humidity': humidity,
            'pressure': pressure
        }
