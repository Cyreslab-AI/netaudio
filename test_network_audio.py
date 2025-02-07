#!/usr/bin/env python3
"""Simple network traffic to audio test."""

import sys
import sounddevice as sd
import numpy as np
from scapy.all import sniff
import threading
import queue

# Global audio parameters
SAMPLE_RATE = 44100
BUFFER_SIZE = 1024
audio_queue = queue.Queue()
running = True

def generate_tone(frequency=440.0, duration=0.1):
    """Generate a simple sine wave."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    return 0.5 * np.sin(2 * np.pi * frequency * t)

def audio_callback(outdata, frames, time, status):
    """Audio stream callback."""
    try:
        data = audio_queue.get_nowait()
        outdata[:len(data)] = data.reshape(-1, 1)
        outdata[len(data):] = 0
    except queue.Empty:
        outdata.fill(0)

def packet_callback(packet):
    """Handle captured packets."""
    # Generate different tones based on packet size
    size = len(packet)
    freq = 220 + (size % 1000)
    tone = generate_tone(freq)
    audio_queue.put(tone)
    print(f"\rPacket size: {size}, Frequency: {freq:.1f} Hz", end="")

def main():
    print("Starting audio stream...")
    try:
        with sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=audio_callback,
            blocksize=BUFFER_SIZE
        ):
            print("Monitoring network traffic on lo0...")
            print("Press Ctrl+C to stop")
            
            # Start packet capture
            sniff(iface="lo0", prn=packet_callback, store=False)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
