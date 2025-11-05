import time, logging, board, adafruit_dht
logger = logging.getLogger(__name__)

class environmental_module:
    """DHT11 réel sur GPIO4 (pin 7) — température & humidité"""
    def __init__(self, config_file="config.json"):
        self.dht = adafruit_dht.DHT11(board.D4, use_pulseio=False)

    def _read_once(self):
        t = self.dht.temperature
        h = self.dht.humidity
        if t is None or h is None:
            raise RuntimeError("DHT11 returned None")
        return float(t), float(h)

    def get_environmental_data(self):
        last_err = None
        for _ in range(6):
            try:
                t, h = self._read_once()
                return {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "temperature": t,
                    "humidity": h
                }
            except RuntimeError as e:
                last_err = e
                time.sleep(2.0)
        logger.warning(f"DHT11 read failed after retries: {last_err}")
        return {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
