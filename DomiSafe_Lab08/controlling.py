import time
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

# ==== Adafruit IO (replace with your NEW regenerated key) ====

# ==== Feed ====
FEED = f"{AIO_USERNAME}/feeds/buzzer"   # expects ON/OFF (or 1/0, true/false)

# ==== Buzzer on GPIO 18 (passive piezo) ====
PIN = 18
FREQ = 1000  # 1 kHz tone

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)
pwm = GPIO.PWM(PIN, FREQ)
is_on = False

def buzz(on: bool):
    global is_on
    if on and not is_on:
        pwm.start(50)  # 50% duty
        is_on = True
    elif not on and is_on:
        pwm.stop()
        is_on = False

# ---- MQTT callbacks ----
def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected:", rc)
    client.subscribe(FEED)

def on_message(client, userdata, msg):
    raw = msg.payload.decode().strip().lower()
    print(f"Feed {msg.topic} ? {raw}")
    truthy = {"on","1","true","yes"}
    falsy  = {"off","0","false","no"}

    if raw in truthy:
        buzz(True)
    elif raw in falsy:
        buzz(False)
    # else ignore unexpected values

def cleanup():
    buzz(False)
    GPIO.cleanup()

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
    cleanup()
