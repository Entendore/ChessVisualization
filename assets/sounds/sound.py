import numpy as np
import sounddevice as sd

def play_tone(frequency=440.0, duration=0.15, volume=0.4, waveform="square"):
    samplerate = 44100
    t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)

    if waveform == "square":
        wave = np.sign(np.sin(2 * np.pi * frequency * t))  # retro beeps
    elif waveform == "saw":
        wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))  # buzzy
    elif waveform == "triangle":
        wave = 2 * np.abs(2 * (t * frequency - np.floor(0.5 + t * frequency))) - 1
    else:  # default sine
        wave = np.sin(2 * np.pi * frequency * t)

    wave *= volume
    sd.play(wave, samplerate)
    sd.wait()

def arpeggio(base_freq, steps=[0, 4, 7], speed=0.05):
    """Play a fast little chiptune arpeggio"""
    for step in steps:
        play_tone(base_freq * (2 ** (step/12)), duration=speed, waveform="square")

# 🎵 Chess "retro" sound mappings
def chess_sound(event="move"):
    if event == "move":  # simple bleep
        play_tone(600, 0.08, 0.4, "square")
    elif event == "capture":  # crunchy downward blip
        play_tone(800, 0.07, 0.4, "saw")
        play_tone(400, 0.1, 0.4, "saw")
    elif event == "check":  # urgent double-beep
        play_tone(700, 0.08, 0.4, "square")
        play_tone(700, 0.08, 0.4, "square")
    elif event == "castle":  # happy arpeggio
        arpeggio(500, [0, 4, 7, 12])
    elif event == "promote":  # victory jingle
        arpeggio(440, [0, 4, 7])
        arpeggio(660, [0, 3, 7])
    elif event == "game_over":  # descending "fail" tone
        for f in [600, 400, 200]:
            play_tone(f, 0.12, 0.4, "square")