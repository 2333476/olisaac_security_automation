import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import threading
import time

# ==== Adafruit IO credentials ====

# ==== Feed ====
FEED = f"{AIO_USERNAME}/feeds/leds_control"

# ==== GPIO pins (BCM) ====
PINS = {"red": 17, "yellow": 27, "green": 22}

GPIO.setmode(GPIO.BCM)
for pin in PINS.values():
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

TRUTHY = {"on", "1", "true", "yes"}
FALSY = {"off", "0", "false", "no"}

pattern_thread = None
pattern_running = False


def set_led(name: str, on: bool):
    pin = PINS.get(name)
    if pin is not None:
        GPIO.output(pin, GPIO.HIGH if on else GPIO.LOW)


# ----- PATTERN (SIREN) -----
def led_pattern():
    """Run LED pattern in a loop until stopped."""
    global pattern_running
    print("Pattern started!")
    while pattern_running:
        # Example pattern: Red/Green alternate like a siren
        GPIO.output(PINS["red"], True)
        GPIO.output(PINS["green"], False)
        time.sleep(0.3)
        GPIO.output(PINS["red"], False)
        GPIO.output(PINS["green"], True)
        time.sleep(0.3)
        # Blink yellow in between
        GPIO.output(PINS["yellow"], True)
        time.sleep(0.1)
        GPIO.output(PINS["yellow"], False)
    # When stopped, turn off all LEDs
    for p in PINS.values():
        GPIO.output(p, GPIO.LOW)
    print("Pattern stopped!")


def start_pattern():
    global pattern_thread, pattern_running
    if not pattern_running:
        pattern_running = True
        pattern_thread = threading.Thread(target=led_pattern, daemon=True)
        pattern_thread.start()


def stop_pattern():
    global pattern_running
    pattern_running = False


# ----- COMMAND PARSING -----
def handle_command(cmd: str):
    """Parse commands like 'red:on' or 'pattern:on'"""
    global pattern_running
    if not cmd:
        return

    parts = [p.strip() for p in cmd.split(",") if p.strip()]
    for part in parts:
        if ":" not in part:
            continue
        target, action = [x.strip().lower() for x in part.split(":", 1)]

        # Handle pattern mode
        if target == "pattern":
            if action in TRUTHY:
                start_pattern()
            elif action in FALSY:
                stop_pattern()
            continue

        # Handle normal LEDs
        state = None
        if action in TRUTHY:
            state = True
        elif action in FALSY:
            state = False

        if state is not None:
            if target == "all":
                for n in PINS:
                    set_led(n, state)
            elif target in PINS:
                set_led(target, state)


def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected to Adafruit IO:", rc)
    client.subscribe(FEED)


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8").strip()
    print(f"{msg.topic} → {payload}")
    handle_command(payload)


# ----- MQTT SETUP -----
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(AIO_USERNAME, AIO_KEY)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("io.adafruit.com", 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    pass
finally:
    stop_pattern()
    for p in PINS.values():
        GPIO.output(p, GPIO.LOW)
    GPIO.cleanup()
