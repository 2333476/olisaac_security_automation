# Plays "Jingle Bells" on a passive piezo buzzer connected to GPIO 18 (pin 12)
# Wiring: Buzzer (+) -> GPIO 18, Buzzer (-) -> GND
# Requires: sudo apt install python3-rpi.gpio  (or pip install RPi.GPIO)

import time
import RPi.GPIO as GPIO

BUZZER_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Create PWM object (frequency will be changed per note)
pwm = GPIO.PWM(BUZZER_PIN, 440)

# Note frequencies (Hz) – 4th/5th octave
NOTES = {
    "B3": 247, "C4": 262, "CS4": 277, "D4": 294, "DS4": 311, "E4": 330, "F4": 349,
    "FS4": 370, "G4": 392, "GS4": 415, "A4": 440, "AS4": 466, "B4": 494,
    "C5": 523, "CS5": 554, "D5": 587, "DS5": 622, "E5": 659, "F5": 698,
    "FS5": 740, "G5": 784, "GS5": 831, "A5": 880, "REST": 0
}

# Tempo settings
BPM = 180            # higher = faster
BEAT = 60.0 / BPM    # quarter note length in seconds
STACCATO = 0.85      # fraction of each note to sound (rest fills the remainder)

# Melody for "Jingle Bells" (first verse & chorus)
# Format: (note_name, note_length_in_beats)
JINGLE_BELLS = [
    # Dashing through the snow...
    ("E5",1), ("E5",1), ("E5",2),
    ("E5",1), ("E5",1), ("E5",2),
    ("E5",1), ("G5",1), ("C5",1), ("D5",1),
    ("E5",4),

    ("F5",1), ("F5",1), ("F5",1), ("F5",1),
    ("F5",1), ("E5",1), ("E5",1), ("E5",1),
    ("E5",1), ("D5",1), ("D5",1), ("E5",1),
    ("D5",2), ("G5",2),

    # Jingle bells, jingle bells...
    ("E5",1), ("E5",1), ("E5",1), ("E5",1),
    ("E5",1), ("E5",1), ("E5",1), ("G5",1),
    ("C5",1), ("D5",1), ("E5",2),

    ("F5",1), ("F5",1), ("F5",1), ("F5",1),
    ("F5",1), ("E5",1), ("E5",1), ("E5",1),
    ("G5",1), ("G5",1), ("F5",1), ("D5",1),
    ("C5",4),
]

def play_note(freq_hz: int, beats: float):
    duration = BEAT * beats
    on_time = duration * STACCATO
    off_time = duration - on_time

    if freq_hz <= 0:
        # rest
        time.sleep(duration)
        return

    pwm.ChangeFrequency(freq_hz)
    pwm.start(50)  # 50% duty cycle
    time.sleep(on_time)
    pwm.stop()
    if off_time > 0:
        time.sleep(off_time)

def play_song(score):
    for note, beats in score:
        freq = NOTES.get(note, 0)
        play_note(freq, beats)

try:
    print("Playing: Jingle Bells 🎄")
    play_song(JINGLE_BELLS)
    print("Done.")
except KeyboardInterrupt:
    pass
finally:
    pwm.stop()
    GPIO.cleanup()
