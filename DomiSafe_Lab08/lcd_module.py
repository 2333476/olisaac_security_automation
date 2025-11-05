# lcd_module.py
# 16x2/20x4 HD44780 LCD with I2C (PCF8574) backpack
# Subscribes to Adafruit IO: lcd_text (free text) + lcd_alert (ON/OFF preset)

from RPLCD.i2c import CharLCD
import paho.mqtt.client as mqtt

class LCDController:
    def __init__(self, config: dict):
        # ---- Config / defaults ----
        self.username = config.get("ADAFRUIT_IO_USERNAME")
        self.key = config.get("ADAFRUIT_IO_KEY")
        self.broker = config.get("MQTT_BROKER", "io.adafruit.com")
        self.port = config.get("MQTT_PORT", 1883)

        # Feeds (customizable in config.json if you want)
        self.feed_text  = f'{self.username}/feeds/' + config.get("LCD_TEXT_FEED", "lcd_text")
        self.feed_alert = f'{self.username}/feeds/' + config.get("LCD_ALERT_FEED", "lcd_alert")

        # LCD params
        self.addr = int(config.get("LCD_ADDRESS", 0x27))
        self.cols = int(config.get("LCD_COLS", 16))
        self.rows = int(config.get("LCD_ROWS", 2))
        self.preset_message = config.get("LCD_PRESET_MESSAGE", "Get out of my house")

        # ---- LCD ----
        self.lcd = CharLCD(
            i2c_expander='PCF8574',
            address=self.addr,
            port=1,
            cols=self.cols,
            rows=self.rows,
            charmap='A02',
            auto_linebreaks=True,
            backlight_enabled=True,
        )

        # ---- State ----
        self.alert_active = False
        self.last_normal_text = ""

        # ---- MQTT ----
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(self.username, self.key)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ---------- Public API ----------
    def start(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def stop(self):
        try:
            self._clear()
            self.lcd.backlight_enabled = False
        finally:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
            # Do not cleanup I2C device file; LCD library handles it

    # ---------- Internals ----------
    def _show(self, text: str):
        self.lcd.clear()
        parts = (text or "").split("\n", 1)
        self.lcd.write_string(parts[0][:self.cols])
        if len(parts) > 1:
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(parts[1][:self.cols])

    def _clear(self):
        self.lcd.clear()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        print("LCDController connected:", rc)
        client.subscribe(self.feed_text)
        client.subscribe(self.feed_alert)

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode().strip()

        if topic == self.feed_text:
            self.last_normal_text = payload
            if not self.alert_active:
                self._show(self.last_normal_text)

        elif topic == self.feed_alert:
            val = payload.lower()
            if val in {"on", "1", "true", "yes"}:
                self.alert_active = True
                self._show(self.preset_message)
            elif val in {"off", "0", "false", "no"}:
                self.alert_active = False
                self._show(self.last_normal_text)
