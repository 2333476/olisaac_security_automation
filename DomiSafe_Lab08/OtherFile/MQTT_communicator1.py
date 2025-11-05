import paho.mqtt.client as mqtt
import json, logging

logger = logging.getLogger(__name__)

class MQTT_communicator:
    def __init__(self, config_file="config.json"):
        with open(config_file) as f:
            self.config = json.load(f)

        self.client = mqtt.Client()
        self.client.username_pw_set(
            self.config["ADAFRUIT_IO_USERNAME"],
            self.config["ADAFRUIT_IO_KEY"]
        )
        self.client.connect(
            self.config["MQTT_BROKER"],
            self.config["MQTT_PORT"],
            self.config["MQTT_KEEPALIVE"]
        )

    def send_to_adafruit_io(self, feed, value):
        topic = f"{self.config['ADAFRUIT_IO_USERNAME']}/feeds/{feed}"
        try:
            self.client.publish(topic, value)
            logger.info(f"Published {value} to {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False

