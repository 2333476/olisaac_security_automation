# buzzer_module.py
# Passive piezo on GPIO 18; listens to Adafruit IO feed "<username>/feeds/buzzer"
# Expects values: ON/OFF (also accepts 1/0, true/false)

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

class BuzzerController:
    def __init__(self, config: dict):
        # --- Config / defaults ---
        self.username = config.get("ADAFRUIT_IO_USERNAME")
        self.key = config.get("ADAFRUIT_IO_KEY")
        self.broker = config.get("MQTT_BROKER", "io.adafruit.com")
        self.port = config.get("MQTT_PORT", 1883)
        feed_name = config.get("BUZZER_FEED", "buzzer")   # dashboard toggle bound to this feed
        self.feed = f"{self.username}/feeds/{feed_name}"

        self.pin = int(config.get("BUZZER_PIN", 18))
        self.freq = int(config.get("BUZZER_FREQ", 1000))  # Hz

        # --- GPIO / PWM ---
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, self.freq)
        self.is_on = False

        # --- MQTT client ---
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(self.username, self.key)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ---- Public API ----
    def start(self):
        # Non-blocking network loop
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def stop(self):
        # Turn off, stop network, release GPIO
        try:
            self._buzz(False)
        finally:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
            GPIO.cleanup(self.pin)  # only our pin

    # ---- Internal helpers / callbacks ----
    def _buzz(self, on: bool):
        if on and not self.is_on:
            self.pwm.start(50)    # 50% duty
            self.is_on = True
        elif not on and self.is_on:
            self.pwm.stop()
            self.is_on = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        print("BuzzerController connected:", rc)
        client.subscribe(self.feed)

    def _on_message(self, client, userdata, msg):
        raw = msg.payload.decode().strip().lower()
        print(f"[buzzer] {msg.topic} → {raw}")
        truthy = {"on", "1", "true", "yes"}
        falsy  = {"off", "0", "false", "no"}

        if raw in truthy:
            self._buzz(True)
        elif raw in falsy:
            self._buzz(False)
        # else: ignore unexpected values
