# Name: Isaac Nachate, ID: 1725258
# File: security_module.py â€” DomiSafe Lab 08 (USB camera version)

import json
import time
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os

import board
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

        # Create folder for captured images
        self.image_dir = 'captured_images'
        Path(self.image_dir).mkdir(parents=True, exist_ok=True)

        # Initialize PIR motion sensor on GPIO D6
        self.pir = digitalio.DigitalInOut(board.D6)
        self.pir.direction = digitalio.Direction.INPUT

        # âœ… USB Camera setup (OpenCV)
        self.use_usb_cam = True
        if self.use_usb_cam:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            logger.info("USB camera initialized successfully.")
        else:
            logger.warning("No camera initialized. Using fallback image capture mode.")

        # Keep track of last alert times (for cooldown)
        self.last_alert_time = {}

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
        """Generate and collect real security sensor data (PIR + optional camera + email alert)"""
        # Smoke detection (simulated for this lab)
        smoke_detected = random.random() < 0.001

        # Read motion sensor (GPIO D6)
        self.pir.direction = digitalio.Direction.INPUT
        motion_detected = self.pir.value

        if motion_detected:
            print("âš ï¸ Motion detected!")
        else:
            print("No motion")

        image_path = None
        if motion_detected and self.config.get("camera_enabled", True):
            image_path = self.capture_image()

            # Send alert with image
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
        """Capture an image using USB webcam (or create placeholder on failure)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = f"{self.image_dir}/motion_{timestamp}.jpg"

        try:
            if self.use_usb_cam:
                ok, frame = self.cap.read()
                if not ok:
                    raise RuntimeError("USB camera capture failed")
                cv2.imwrite(image_path, frame)
                logger.info(f"Image captured: {image_path}")
                return image_path
            else:
                raise RuntimeError("Camera not initialized")

        except Exception as e:
            logger.warning(f"Camera capture failed: {e}")
            # Fallback: create a small text file instead
            image_path = f"{self.image_dir}/motion_{timestamp}.txt"
            with open(image_path, 'w') as f:
                f.write(f"Motion detected at {datetime.now().isoformat()}")
            return image_path

    def send_smtp2go_alert(self, alert_type, message="", image_path=None):
        """Send email alert via SMTP2GO with optional image attachment"""
        ALERT_COOLDOWN = 300  # 5 minutes between alerts
        now = time.time()

        # Cooldown check
        if alert_type in self.last_alert_time:
            if now - self.last_alert_time[alert_type] < ALERT_COOLDOWN:
                print(f"â³ Alert cooldown active for {alert_type}, skipping...")
                return False

        try:
            smtp_host = self.config["SMTP_HOST"]
            smtp_port = int(self.config["SMTP_PORT"])
            smtp_user = self.config["SMTP_USER"]
            smtp_pass = self.config["SMTP_PASS"]
            sender = self.config["ALERT_FROM"]
            recipient = self.config["ALERT_TO"]

            if not all([smtp_user, smtp_pass, sender, recipient]):
                raise ValueError("Missing SMTP2GO credentials in config.json")

            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = f"ðŸš¨ DomiSafe Alert: {alert_type}"

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

            if image_path and Path(image_path).exists():
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename=Path(image_path).name)
                    msg.attach(img)
                print(f"ðŸ“Ž Attached image: {image_path}")

            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            self.last_alert_time[alert_type] = now
            print(f"âœ… Email alert sent via SMTP2GO: {alert_type}")
            return True

        except Exception as e:
            print(f"âŒ Failed to send email via SMTP2GO: {e}")
            return False

    def cleanup(self):
        """Release camera safely when program stops"""
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
            logger.info("USB camera released successfully.")
