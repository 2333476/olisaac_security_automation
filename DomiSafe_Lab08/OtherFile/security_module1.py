import time
import json
import os
import logging
import board
from digitalio import DigitalInOut, Direction, Pull
import cv2

logger = logging.getLogger(__name__)

try:
    # Teste la presence dune camera USB
    cap = cv2.VideoCapture(0)
    USB_CAMERA_AVAILABLE = cap.isOpened()
    cap.release()
except Exception as e:
    logger.warning(f"Camera USB non disponible: {e}")
    USB_CAMERA_AVAILABLE = False


class security_module:
    
    def __init__(self, config_file="config.json"):
        with open(config_file) as f:
            self.config = json.load(f)

        self.pir = DigitalInOut(board.D17)
        self.pir.direction = Direction.INPUT

        self.smoke = DigitalInOut(board.D26)
        self.smoke.direction = Direction.INPUT
        self.smoke.pull = Pull.UP 

        self.buzzer = DigitalInOut(board.D18)
        self.buzzer.direction = Direction.OUTPUT
        self.buzzer.value = False

        self.camera_enabled = bool(self.config.get("camera_enabled", False))
        self.cap = None
        if self.camera_enabled and USB_CAMERA_AVAILABLE:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise RuntimeError("Impossible douvrir la camera USB.")
                logger.info("Camera USB demarre")
            except Exception as e:
                logger.error(f"Erreur camera: {e}")
                self.cap = None

    def _capture_image(self):
        if not (self.camera_enabled and self.cap):
            return None
        ts = time.strftime("%Y%m%d_%H%M%S")
        name = f"{ts}_motion.jpg"
        try:
            ret, frame = self.cap.read()
            if not ret:
                raise RuntimeError("Capture echoue")
            cv2.imwrite(name, frame)
            logger.info(f"Image capture : {name}")
            return os.path.abspath(name)
        except Exception as e:
            logger.error(f"Erreur capture image: {e}")
            return None

    def get_security_data(self):
        motion = bool(self.pir.value)
        smoke_alarm = (self.smoke.value == 0)
        image = None

        if motion or smoke_alarm:
            logger.info("  Detection : activation buzzer")
            self.buzzer.value = True
            time.sleep(0.3)
            self.buzzer.value = False

            if motion:
                image = self._capture_image()

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "motion_detected": motion,
            "smoke_detected": smoke_alarm,
            "image_path": image
        }
