


import json
import time
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os


import board

from picamera2 import Picamera2
import cv2
import digitalio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class security_module:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        # initialize motion sensor
        self.pir = digitalio.DigitalInOut(board.D6)
        self.pir.direction = digitalio.Direction.INPUT

        # Initialize Pi Camera
        self.picam2 = Picamera2()
        self.picam2.start()
        self.image_dir = 'captured_images'

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        default_config = {
            "ADAFRUIT_IO_USERNAME": "username",
            "ADAFRUIT_IO_KEY": "userkey",
            "MQTT_BROKER": "io.adafruit.com",
            "MQTT_PORT": 1883,
            "MQTT_KEEPALIVE": 60,
            "devices": ["living_room_light", "bedroom_fan", "front_door", "garage_door"],
            "camera_enabled": True,
            "capturing_interval": 900,
            "flushing_interval": 10,
            "sync_interval": 300
        }

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return default_config





    def get_security_data(self):
        """Generate simulated security sensor data"""
        # Motion detection probability (higher during day)
        # hour = datetime.now().hour
        # motion_prob = 0.1 if 22 <= hour or hour <= 6 else 0.3
        # motion_detected = random.random() < motion_prob

        # Smoke detection (very rare)
        smoke_detected = random.random() < 0.001
        self.pir.direction = digitalio.Direction.INPUT
        #print('self.pir.value : ' , self.pir.value)
        if self.pir.value:   # HIGH when motion detected
          print("Motion detected!")
        else:
          print("No motion")
        motion_detected = self.pir.value
        image_path = None
        if motion_detected and self.config['camera_enabled']:
            image_path = self.capture_image()
            # Send email alert with image
            self.send_smtp2go_alert(
                "Motion Detected",
                "Motion sensor triggered",
                image_path
            )

        return {
            'timestamp': datetime.now().isoformat(),
            'motion_detected': motion_detected,
            'smoke_detected': smoke_detected,
            'image_path': image_path
        }

    def capture_image(self):
        """Simulate camera image capture"""
        try:
            # Try to use actual camera if available
            frame = self.picam2.capture_array()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = f"{self.image_dir}/motion_{timestamp}.jpg"
            cv2.imwrite(image_path, frame)
            logger.info(f"Image captured: {image_path}")
            return image_path
        except Exception as e:
            logger.warning(f"Camera capture failed: {e}")

        # Fallback: create a placeholder image file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = f"{self.image_dir}/motion_{timestamp}.txt"
        with open(image_path, 'w') as f:
            f.write(f"Motion detected at {datetime.now().isoformat()}")
        return image_path



    def send_smtp2go_alert(self, alert_type, message="", image_path=None):
        """Send email alert via SMTP2GO with optional image attachment"""
        #global last_alert_time
        last_alert_time = {}
        ALERT_COOLDOWN = 300  # 5 minutes between alerts
        # Check cooldown
        now = time.time()
        if alert_type in last_alert_time:
            if now - last_alert_time[alert_type] < ALERT_COOLDOWN:
                print(f"⏳ Alert cooldown active for {alert_type}, skipping...")
                return False
        try:
            # SMTP2GO configuration from .env
            smtp_host = self.config["SMTP_HOST"]
            smtp_port = int(self.config["SMTP_PORT"])
            smtp_user = self.config["SMTP_USER"]
            smtp_pass =  self.config["SMTP_PASS"]
            sender = self.config["ALERT_FROM"]
            recipient = self.config["ALERT_TO"]

            if not all([smtp_user, smtp_pass, sender, recipient]):
                raise ValueError("Missing SMTP2GO credentials in .env file")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = f"🚨 DomiSafe Alert: {alert_type}"

            # Email body
            body = f"""
                DomiSafe Security Alert

                Alert Type: {alert_type}
                Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                Location: Home Security System

                {message}

                ---
                This is an automated alert from your DomiSafe IoT system.
            """
            msg.attach(MIMEText(body, 'plain'))

            # Attach image if provided
            if image_path and Path(image_path).exists():
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=Path(image_path).name
                    )
                    msg.attach(img)
                print(f"📎 Attached image: {image_path}")

            # Send via SMTP2GO
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            print(f"✅ Email alert sent via SMTP2GO: {alert_type}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email via SMTP2GO: {e}")
            return False

