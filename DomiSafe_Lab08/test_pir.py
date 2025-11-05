# test_pir.py
import time, board, digitalio
pir = digitalio.DigitalInOut(board.D6)  # change if you wired another pin
pir.direction = digitalio.Direction.INPUT

print("Warming up 60s…")
time.sleep(60)
print("Ready. Wave your hand in front of the PIR.")

while True:
    print("Motion!" if pir.value else "No motion")
    time.sleep(0.5)
