import json, logging
logger = logging.getLogger(__name__)

class device_control_module:
    def __init__(self, config_file="config.json"):
        with open(config_file) as f:
            self.config = json.load(f)

    def get_device_status(self):
        devices = self.config.get("devices", [])
        return {device: "ON" for device in devices}
