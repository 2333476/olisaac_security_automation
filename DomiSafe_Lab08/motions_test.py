import board
import digitalio
import time
# Use GPIO17
pir = digitalio.DigitalInOut(board.D6)
pir.direction = digitalio.Direction.INPUT
print("PIR Motion Sensor Test (press Ctrl+C to stop)")
while True:
 if pir.value: # HIGH when motion detected
    print("Motion detected!")
 else:
    print("No motion")
 time.sleep(1)
