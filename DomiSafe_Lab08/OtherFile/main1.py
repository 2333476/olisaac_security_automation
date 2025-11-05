# DomiSafe Lab08 — Main (vraies données)
import json, time, logging, os, threading
from datetime import datetime
from pathlib import Path

from MQTT_communicator import MQTT_communicator
from environmental_module import environmental_module
from security_module import security_module
from device_control_module import device_control_module

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Feeds à créer une fois sur Adafruit IO si pas déjà là
ENV_FEEDS = {"temperature": "temperature", "humidity": "humidity"}
SECURITY_FEEDS = {"motion_count": "motion_feed", "smoke_count": "smoke_feed"}

class DomiSafeApp:
    def __init__(self, config_file='config.json'):
        self.config = self._load_config(config_file)
        self.security_check_interval = self.config.get("security_check_interval", 5)
        self.security_send_interval = self.config.get("security_send_interval", 60)
        self.env_interval = self.config.get("env_interval", 30)

        self.running = True
        self.mqtt_agent = MQTT_communicator(config_file)
        self.env_data = environmental_module(config_file)
        self.security_data = security_module(config_file)
        self.device_control = device_control_module(config_file)

    def _load_config(self, path):
        try:
            with open(path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("config.json not found!")
            return {}

    def send_to_cloud(self, data, feeds):
        """Publie les champs présents dans 'data' vers les feeds correspondants."""
        ok_all = True
        ts = data.get("timestamp")
        logger.info(f"Processing reading from {ts}")
        for field, feed in feeds.items():
            if field not in data:
                continue
            val = data[field]
            ok = self.mqtt_agent.send_to_adafruit_io(feed, val)
            ok_all = ok_all and ok
            time.sleep(0.2)
        return ok_all

    def collect_environmental_data(self, now, timers, fh_env):
        if now - timers['env_check'] >= self.env_interval:
            env = self.env_data.get_environmental_data()
            fh_env.write(json.dumps(env) + "\n")
            fh_env.flush()
            self.send_to_cloud(env, ENV_FEEDS)
            logger.info(f"Environmental data: {env}")
            timers['env_check'] = now

    def collect_security_data(self, now, timers, counters, fh_sec):
        # échantillonnage PIR/fumée
        if now - timers['security_check'] >= self.security_check_interval:
            sec = self.security_data.get_security_data()
            if sec.get('motion_detected'):
                counters['motion'] += 1
                logger.warning("Motion detected!")
            if sec.get('smoke_detected'):
                counters['smoke'] += 1
                logger.warning("Smoke alarm!")
            fh_sec.write(json.dumps(sec) + "\n")
            fh_sec.flush()
            timers['security_check'] = now

        # résumé périodique vers Adafruit IO
        if now - timers['security_send'] >= self.security_send_interval:
            summary = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "motion_count": counters['motion'],
                "smoke_count": counters['smoke']
            }
            self.send_to_cloud(summary, SECURITY_FEEDS)
            counters['motion'] = 0
            counters['smoke'] = 0
            timers['security_send'] = now

    def data_collection_loop(self):
        ts = datetime.now().strftime("%Y%m%d")
        env_file = f"{ts}_environmental_data.txt"
        sec_file = f"{ts}_security_data.txt"
        dev_file = f"{ts}_device_status.txt"
        for p in (env_file, sec_file, dev_file):
            Path(p).touch(exist_ok=True)
        logger.info(f"Writing to:\n  {os.path.abspath(env_file)}\n  {os.path.abspath(sec_file)}\n  {os.path.abspath(dev_file)}")

        with open(env_file, "a", buffering=1) as fenv, \
             open(sec_file, "a", buffering=1) as fsec, \
             open(dev_file, "a", buffering=1) as fdev:

            timers = {"env_check": 0, "security_check": 0, "security_send": 0}
            counters = {"motion": 0, "smoke": 0}

            while self.running:
                now = time.time()
                try:
                    self.collect_security_data(now, timers, counters, fsec)
                    self.collect_environmental_data(now, timers, fenv)
                    time.sleep(self.security_check_interval)
                except Exception as e:
                    logger.error(f"Loop error: {e}", exc_info=True)
                    time.sleep(2)

    def start(self):
        logger.info("Starting DomiSafeApp...")
        t = threading.Thread(target=self.data_collection_loop, daemon=True)
        t.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping...")
            self.running = False
            t.join(timeout=5)
            logger.info("Stopped.")

if __name__ == "__main__":
    DomiSafeApp("config.json").start()

