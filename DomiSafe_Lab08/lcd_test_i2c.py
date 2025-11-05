from RPLCD.i2c import CharLCD
import paho.mqtt.client as mqtt

# ---- LCD setup ----
LCD_ADDRESS = 0x27   # from i2cdetect
COLS, ROWS = 16, 2
lcd = CharLCD(i2c_expander='PCF8574', address=LCD_ADDRESS, port=1,
              cols=COLS, rows=ROWS, charmap='A02', auto_linebreaks=True,
              backlight_enabled=True)

# ---- Adafruit IO ----
FEED_TEXT  = f"{AIO_USERNAME}/feeds/lcd_text"
FEED_ALERT = f"{AIO_USERNAME}/feeds/lcd_alert"

# ---- Behavior ----
PRESET_MESSAGE = "Get out of my house"   # shown when alert is ON
alert_active = False
last_normal_text = ""

def show(text: str):
    lcd.clear()
    # fits 16x2; split on '\n' if present
    parts = (text or "").split("\n", 1)
    lcd.write_string(parts[0][:COLS])
    if len(parts) > 1:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(parts[1][:COLS])

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected:", rc)
    client.subscribe(FEED_TEXT)
    client.subscribe(FEED_ALERT)

def on_message(client, userdata, msg):
    global alert_active, last_normal_text
    topic = msg.topic
    payload = msg.payload.decode().strip()

    if topic == FEED_TEXT:
        last_normal_text = payload
        if not alert_active:
            show(last_normal_text)

    elif topic == FEED_ALERT:
        val = payload.lower()
        if val in {"on", "1", "true", "yes"}:
            alert_active = True
            show(PRESET_MESSAGE)
        elif val in {"off", "0", "false", "no"}:
            alert_active = False
            show(last_normal_text)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(AIO_USERNAME, AIO_KEY)
client.on_connect = on_connect
client.on_message = on_message
client.connect("io.adafruit.com", 1883, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    pass
finally:
    lcd.clear()
    lcd.backlight_enabled = False
