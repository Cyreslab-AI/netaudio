import numpy as np
import sounddevice as sd
import time

# Generate a simple sine wave
sample_rate = 44100
duration = 2.0  # seconds
t = np.linspace(0, duration, int(sample_rate * duration))
frequency = 440.0  # A4 note
amplitude = 0.5

# Generate the sine wave
samples = amplitude * np.sin(2 * np.pi * frequency * t)

print("Playing test tone...")
try:
    # Start the audio stream
    with sd.OutputStream(channels=1, samplerate=sample_rate) as stream:
        # Write the samples to the stream
        stream.write(samples.astype(np.float32))
        # Wait for the sound to finish
        time.sleep(duration)
    print("Test tone finished. Did you hear a 2-second beep?")
except Exception as e:
    print(f"Error playing audio: {e}")
