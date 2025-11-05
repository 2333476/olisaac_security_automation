import RPi.GPIO as GPIO
import time

# Use BCM numbering
BUZZER_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

print("Starting buzzer test...")

try:
    # Create a PWM instance at 1 kHz
    buzzer = GPIO.PWM(BUZZER_PIN, 1000)
    buzzer.start(50)  # 50% duty cycle -> ON

    time.sleep(1)  # Buzz for 1 second
    buzzer.stop()

    time.sleep(0.5)
    print("Beeping pattern...")

    # Beep pattern: 3 short buzzes
    for i in range(3):
        buzzer.start(50)
        time.sleep(0.2)
        buzzer.stop()
        time.sleep(0.2)

    print("Test complete.")

except KeyboardInterrupt:
    pass
finally:
    buzzer.stop()
    GPIO.cleanup()
