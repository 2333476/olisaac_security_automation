# led_module.py — minimal single-feed LED controller + pattern mode

import time
import threading
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

TRUTHY = {"on", "1", "true", "yes"}
FALSY  = {"off", "0", "false", "no"}

class LEDController:
    def __init__(self, config: dict):
        # ---- Config (with safe defaults) ----
        self.username = config.get("ADAFRUIT_IO_USERNAME")
        self.key      = config.get("ADAFRUIT_IO_KEY")
        broker        = config.get("MQTT_BROKER", "io.adafruit.com")
        port          = int(config.get("MQTT_PORT", 1883))
        feed_name     = config.get("LEDS_FEED", "leds_control")

        self.feed     = f"{self.username}/feeds/{feed_name}"
        self.broker, self.port = broker, port

        # Pins (BCM)
        self.pins = {
            "red":    int(config.get("LED_RED_PIN", 17)),
            "yellow": int(config.get("LED_YELLOW_PIN", 27)),
            "green":  int(config.get("LED_GREEN_PIN", 22)),
        }

        GPIO.setmode(GPIO.BCM)
        for p in self.pins.values():
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

        # Pattern state
        self._pattern_on = False
        self._pattern_thread = None

        # MQTT
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(self.username, self.key)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ---- Public API ----
    def start(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def stop(self):
        self._stop_pattern()
        try:
            self.client.loop_stop()
            self.client.disconnect()
        finally:
            for p in self.pins.values():
                GPIO.output(p, GPIO.LOW)
            GPIO.cleanup()

    # ---- MQTT ----
    def _on_connect(self, c, *_):
        print("LEDController connected")
        c.subscribe(self.feed)

    def _on_message(self, _c, _u, msg):
        payload = msg.payload.decode().strip()
        print(f"[leds] {payload}")
        self._handle(payload)

    # ---- Command handling ----
    def _handle(self, cmd: str):
        if not cmd:
            return
        for part in [p.strip() for p in cmd.split(",") if p.strip()]:
            if ":" not in part:
                continue
            target, action = [x.strip().lower() for x in part.split(":", 1)]

            if target == "pattern":
                if action in TRUTHY:  self._start_pattern()
                if action in FALSY:   self._stop_pattern()
                continue

            state = True if action in TRUTHY else False if action in FALSY else None
            if state is None:
                continue

            # manual command cancels pattern
            self._stop_pattern()

            if target == "all":
                for name in self.pins: self._set(name, state)
            elif target in self.pins:
                self._set(target, state)

    # ---- Pattern ----
    def _start_pattern(self):
        if self._pattern_on:
            return
        self._pattern_on = True
        self._pattern_thread = threading.Thread(target=self._pattern_loop, daemon=True)
        self._pattern_thread.start()

    def _stop_pattern(self):
        self._pattern_on = False

    def _pattern_loop(self):
        print("Pattern started")
        while self._pattern_on:
            # siren: red<->green, blink yellow
            self._set("red", True);   self._set("green", False); time.sleep(0.3)
            self._set("red", False);  self._set("green", True);  time.sleep(0.3)
            self._set("yellow", True);                          time.sleep(0.1)
            self._set("yellow", False)
        # turn all off when pattern stops
        for n in self.pins: self._set(n, False)
        print("Pattern stopped")

    # ---- GPIO helper ----
    def _set(self, name: str, on: bool):
        GPIO.output(self.pins[name], GPIO.HIGH if on else GPIO.LOW)
