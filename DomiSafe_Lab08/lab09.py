# Isaac Nachate 2333476, Olivier Goudreault 2332923
import RPi.GPIO as GPIO
import time
import sys
import random
import threading

# Initialize
LCD_I2C_ADDR = 0x27  

try:
    from RPLCD.i2c import CharLCD
    _lcd = CharLCD(i2c_expander='PCF8574', address=LCD_I2C_ADDR, port=1,
                   cols=16, rows=2, charmap='A00', auto_linebreaks=True)
    _lcd_ok = True
except Exception as e:
    _lcd = None
    _lcd_ok = False
    print(f"[LCD] RPLCD not available or LCD not found at 0x{LCD_I2C_ADDR:02X}. "
          f"LCD will be simulated. ({e})")

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define your devices (GPIO pins)
DEVICES = {
    'led1': {'pin': 27, 'name': 'Yellow Led', 'state': False},  # Yellow = 27
    'led2': {'pin': 17, 'name': 'Red Led',    'state': False},  # Red    = 17
    'led3': {'pin': 22, 'name': 'Green Led',  'state': False},  # Green  = 22
    'lcd':  {'pin': LCD_I2C_ADDR, 'name': 'LCD 16x2 (I2C)', 'state': False}
}

# Party mode control
party_mode_active = False
party_thread = None

# Initialize GPIO pins (LEDs only)
for device_id, device in DEVICES.items():
    if device_id.startswith('led'):
        GPIO.setup(device['pin'], GPIO.OUT)
        GPIO.output(device['pin'], GPIO.LOW)
    print(f"Initialized {device['name']} on GPIO/I2C {device['pin']}")

# LCD helper
def lcd_show(line1="SmartSecureHome", line2="LCD ON"):
    if _lcd_ok:
        _lcd.clear()
        _lcd.write_string(line1[:16])
        _lcd.crlf()
        _lcd.write_string(line2[:16])
    else:
        print(f"[LCD] {line1} | {line2}")

def lcd_clear():
    if _lcd_ok:
        _lcd.clear()
    else:
        print("[LCD] cleared")

# ===== UI =====
def show_menu():
    print("\n========== SmartSecureHome ==========")
    print("Select a device to toggle:")
    for i, (device_id, device) in enumerate(DEVICES.items(), start=1):
        state_str = "ON" if device['state'] else "OFF"
        print(f"  {i}) {device['name']} [{state_str}] (GPIO/I2C {device['pin']})")
    print("\nCommands:")
    print("  s) Show status")
    print("  a) Turn ALL ON")
    print("  o) Turn ALL OFF")
    print("  p) Toggle PARTY MODE")
    print("  q) Quit")
    print("=====================================")

def toggle_device(device_id):
    device = DEVICES[device_id]
    device['state'] = not device['state']

    if device_id.startswith('led'):
        GPIO.output(device['pin'], GPIO.HIGH if device['state'] else GPIO.LOW)
    elif device_id == 'lcd':
        if device['state']:
            lcd_show("SmartSecureHome", "Hello!")
        else:
            lcd_clear()

    state_str = "ON" if device['state'] else "OFF"
    print(f"✓ {device['name']} turned {state_str}")

def show_status():
    print("\n--- Current Status ---")
    for device_id, device in DEVICES.items():
        state_str = "ON" if device['state'] else "OFF"
        print(f"  {device['name']}: {state_str} (GPIO/I2C {device['pin']})")

def turn_all(state):
    for device_id, device in DEVICES.items():
        device['state'] = state
        if device_id.startswith('led'):
            GPIO.output(device['pin'], GPIO.HIGH if state else GPIO.LOW)
        elif device_id == 'lcd':
            if state:
                lcd_show("All Devices", "Turned ON")
            else:
                lcd_clear()
    print(f"✓ All devices turned {'ON' if state else 'OFF'}")

def party_mode():
    """Party mode - randomly toggle LEDs"""
    global party_mode_active
    led_devices = ['led1', 'led2', 'led3']
    
    print("🎉 PARTY MODE ACTIVATED! 🎉")
    print("Press 'p' again to stop...")
    
    while party_mode_active:
        pattern = random.choice(['random', 'sequence', 'strobe', 'wave'])
        
        if pattern == 'random':
            for _ in range(10):
                if not party_mode_active:
                    break
                led = random.choice(led_devices)
                state = random.choice([True, False])
                DEVICES[led]['state'] = state
                GPIO.output(DEVICES[led]['pin'], GPIO.HIGH if state else GPIO.LOW)
                time.sleep(0.1)
        
        elif pattern == 'sequence':
            for led in led_devices:
                if not party_mode_active:
                    break
                DEVICES[led]['state'] = True
                GPIO.output(DEVICES[led]['pin'], GPIO.HIGH)
                time.sleep(0.2)
                DEVICES[led]['state'] = False
                GPIO.output(DEVICES[led]['pin'], GPIO.LOW)
        
        elif pattern == 'strobe':
            for _ in range(5):
                if not party_mode_active:
                    break
                for led in led_devices:
                    DEVICES[led]['state'] = True
                    GPIO.output(DEVICES[led]['pin'], GPIO.HIGH)
                time.sleep(0.1)
                for led in led_devices:
                    DEVICES[led]['state'] = False
                    GPIO.output(DEVICES[led]['pin'], GPIO.LOW)
                time.sleep(0.1)
        
        elif pattern == 'wave':
            for led in led_devices + led_devices[::-1]:
                if not party_mode_active:
                    break
                DEVICES[led]['state'] = True
                GPIO.output(DEVICES[led]['pin'], GPIO.HIGH)
                time.sleep(0.15)
                DEVICES[led]['state'] = False
                GPIO.output(DEVICES[led]['pin'], GPIO.LOW)
    
    for led in led_devices:
        DEVICES[led]['state'] = False
        GPIO.output(DEVICES[led]['pin'], GPIO.LOW)
    
    print("🎉 Party mode stopped")

def toggle_party_mode():
    global party_mode_active, party_thread
    
    if party_mode_active:
        party_mode_active = False
        if party_thread:
            party_thread.join()
    else:
        party_mode_active = True
        party_thread = threading.Thread(target=party_mode, daemon=True)
        party_thread.start()

def cleanup():
    global party_mode_active
    party_mode_active = False
    print("\nCleaning up GPIO...")
    try:
        lcd_clear()
    except Exception:
        pass
    GPIO.cleanup()
    print("Goodbye!")

def main():
    device_keys = list(DEVICES.keys())
    
    try:
        while True:
            show_menu()
            choice = input("\nEnter command: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 's':
                show_status()
            elif choice == 'a':
                turn_all(True)
            elif choice == 'o':
                turn_all(False)
            elif choice == 'p':
                toggle_party_mode()
            elif choice.isdigit() and 1 <= int(choice) <= len(DEVICES):
                device_id = device_keys[int(choice) - 1]
                toggle_device(device_id)
            else:
                print("❌ Invalid command!")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        cleanup()

if __name__ == '__main__':
    main()
