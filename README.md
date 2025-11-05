# 🏠 IoT Home Automation & Security System

An end-to-end **Raspberry Pi-based** Home Automation and Security System built in **Python**, integrating real-time sensing, motion detection, and cloud connectivity.  
This version uses a **USB camera** (instead of the Pi Camera) and allows users to add **their own Adafruit IO credentials** for secure MQTT communication.

---

## 🌐 System Overview

The system provides **remote monitoring and control** for a small-scale smart home setup.  
It detects motion, measures environmental data (temperature and humidity), and provides live feedback through an **LCD display**, **LED indicators**, and a **buzzer**.

When motion is detected, the **USB camera** captures an image, logs the event locally, and publishes data to **Adafruit IO** for cloud visualization and control.  
Users can view live sensor values and manage actuators from a web dashboard.

---

## ⚙️ Key Features

- 🔵 **Motion Detection:** Detects movement using a PIR sensor.  
- 🌡️ **Environmental Monitoring:** Reads temperature and humidity from the DHT11 sensor.  
- 📸 **USB Camera Support:** Captures images automatically when motion is detected.  
- 💡 **Actuators:**  
  - LED for visual status indication.  
  - Buzzer for audible alerts.  
  - LCD for local display of real-time sensor readings.  
- ☁️ **Cloud Integration:** Publishes data to **Adafruit IO** using **MQTT**.  
- 💾 **Local Data Logging:** Saves daily timestamped logs of all sensor readings and events.  
- 🔐 **Secure Configurations:** Adafruit credentials are stored externally (never committed to GitHub).

---

## 🧩 Technologies Used

| Component | Function |
|------------|-----------|
| **Raspberry Pi 4B** | Central controller |
| **PIR Motion Sensor** | Detects movement |
| **DHT11 Sensor** | Measures temperature and humidity |
| **USB Camera** | Captures photos on motion detection |
| **LED** | Visual indicator |
| **Buzzer** | Audible alert |
| **LCD Display (I2C)** | Shows live temperature, humidity, and system state |
| **Adafruit IO (MQTT)** | Cloud dashboard and remote control |
| **Python 3.x** | Main programming language |

---

## ⚙️ Configuration

Before running the system, you **must** add your own Adafruit IO credentials.  

Example:

```json
{
  "ADAFRUIT_IO_USERNAME": "your_username_here",
  "ADAFRUIT_IO_KEY": "your_key_here",
  "FEEDS": {
    "temperature": "home.temperature",
    "humidity": "home.humidity",
    "motion": "home.motion",
    "led": "home.led",
    "buzzer": "home.buzzer"
  }
}

Edit the configuration file located at:

