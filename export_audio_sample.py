#!/usr/bin/env python3
"""
Export Network Audio Sample

This script generates a 30-second audio sample of simulated network traffic
and exports it to a WAV file.
"""

import sys
import os
import time
import random
import numpy as np
import soundfile as sf
from datetime import datetime

# Define packet types and their characteristics
PACKET_TYPES = {
    "TCP_SYN": {"size_range": (40, 60), "frequency_range": (300, 400), "duration": 0.1},
    "TCP_ACK": {"size_range": (40, 60), "frequency_range": (400, 500), "duration": 0.05},
    "TCP_DATA": {"size_range": (100, 1500), "frequency_range": (200, 800), "duration": 0.2},
    "UDP_SMALL": {"size_range": (50, 200), "frequency_range": (600, 800), "duration": 0.1},
    "UDP_LARGE": {"size_range": (500, 1200), "frequency_range": (400, 600), "duration": 0.15},
    "ICMP": {"size_range": (60, 100), "frequency_range": (900, 1100), "duration": 0.08},
}

# Audio profiles with different characteristics
AUDIO_PROFILES = {
    "ambient": {
        "frequency_scale": 0.5,  # Lower frequencies
        "amplitude": 0.4,        # Quieter
        "reverb": 0.3,           # More reverb
        "waveform": "sine"       # Smoother waveform
    },
    "musical": {
        "frequency_scale": 1.0,
        "amplitude": 0.6,
        "reverb": 0.2,
        "waveform": "triangle"
    },
    "alert": {
        "frequency_scale": 1.2,  # Higher frequencies
        "amplitude": 0.8,        # Louder
        "reverb": 0.1,           # Less reverb
        "waveform": "sawtooth"   # Harsher waveform
    }
}

class SimulatedPacket:
    """Simulated network packet."""

    def __init__(self, packet_type):
        """Initialize with a packet type."""
        self.type = packet_type
        self.timestamp = time.time()

        # Generate random size within the range for this packet type
        size_range = PACKET_TYPES[packet_type]["size_range"]
        self.size = random.randint(size_range[0], size_range[1])

    def __str__(self):
        """String representation."""
        return f"{self.type} packet, {self.size} bytes, {datetime.fromtimestamp(self.timestamp).strftime('%H:%M:%S.%f')[:-3]}"

def generate_sine_wave(frequency, duration, amplitude=0.5, sample_rate=44100):
    """Generate a sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    return amplitude * np.sin(2 * np.pi * frequency * t)

def generate_triangle_wave(frequency, duration, amplitude=0.5, sample_rate=44100):
    """Generate a triangle wave."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    return amplitude * 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - amplitude

def generate_sawtooth_wave(frequency, duration, amplitude=0.5, sample_rate=44100):
    """Generate a sawtooth wave."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    return amplitude * 2 * (t * frequency - np.floor(0.5 + t * frequency))

def apply_reverb(signal, mix=0.3, decay=1.0, sample_rate=44100):
    """Apply a simple reverb effect."""
    if mix == 0:
        return signal

    # Create a simple delay-based reverb
    delay_samples = int(0.05 * sample_rate)  # 50ms delay
    decay_factor = np.exp(-np.arange(len(signal)) / (decay * sample_rate))

    reverb = np.zeros_like(signal)
    if delay_samples < len(signal):
        reverb[delay_samples:] = signal[:-delay_samples] * decay_factor[:-delay_samples]

    return (1 - mix) * signal + mix * reverb

def packet_to_audio(packet, profile="ambient", sample_rate=44100):
    """Convert a packet to audio based on its characteristics and the selected profile."""
    # Get packet type characteristics
    packet_info = PACKET_TYPES[packet.type]

    # Get profile characteristics
    profile_info = AUDIO_PROFILES[profile]

    # Map packet size to frequency within the range for this packet type
    size_range = packet_info["size_range"]
    freq_range = packet_info["frequency_range"]

    # Normalize size to 0-1 range
    normalized_size = (packet.size - size_range[0]) / (size_range[1] - size_range[0])

    # Map to frequency range and apply profile scaling
    frequency = freq_range[0] + normalized_size * (freq_range[1] - freq_range[0])
    frequency *= profile_info["frequency_scale"]

    # Get duration and amplitude
    duration = packet_info["duration"]
    amplitude = profile_info["amplitude"]

    # Generate waveform based on profile
    if profile_info["waveform"] == "sine":
        signal = generate_sine_wave(frequency, duration, amplitude, sample_rate)
    elif profile_info["waveform"] == "triangle":
        signal = generate_triangle_wave(frequency, duration, amplitude, sample_rate)
    elif profile_info["waveform"] == "sawtooth":
        signal = generate_sawtooth_wave(frequency, duration, amplitude, sample_rate)
    else:
        signal = generate_sine_wave(frequency, duration, amplitude, sample_rate)

    # Apply reverb
    signal = apply_reverb(signal, profile_info["reverb"], 1.0, sample_rate)

    return signal, frequency

def export_audio_sample(output_file, duration=30, profile="ambient", pattern="random", sample_rate=44100):
    """Generate a network traffic audio sample and export it to a WAV file.

    Args:
        output_file: Path to output WAV file
        duration: Sample duration in seconds
        profile: Audio profile to use
        pattern: Traffic pattern (random, web_browsing, port_scan, data_transfer)
        sample_rate: Audio sample rate in Hz
    """
    print(f"Generating {duration}-second audio sample with {profile} profile")
    print(f"Pattern: {pattern}")
    print(f"Output file: {output_file}")

    # Create an empty audio buffer
    audio_buffer = np.array([], dtype=np.float32)

    # Simulate network traffic
    start_time = time.time()
    packet_count = 0

    # Continue until we have enough audio
    while len(audio_buffer) / sample_rate < duration:
        # Generate packet based on pattern
        if pattern == "random":
            packet_type = random.choice(list(PACKET_TYPES.keys()))
        elif pattern == "web_browsing":
            # Simulate web browsing: mostly TCP, some small UDP
            packet_type = random.choices(
                ["TCP_SYN", "TCP_ACK", "TCP_DATA", "UDP_SMALL"],
                weights=[0.1, 0.3, 0.5, 0.1]
            )[0]
        elif pattern == "port_scan":
            # Simulate port scan: many TCP SYN packets
            packet_type = random.choices(
                ["TCP_SYN", "TCP_ACK"],
                weights=[0.9, 0.1]
            )[0]
        elif pattern == "data_transfer":
            # Simulate data transfer: mostly large TCP data packets
            packet_type = random.choices(
                ["TCP_SYN", "TCP_ACK", "TCP_DATA"],
                weights=[0.05, 0.15, 0.8]
            )[0]
        else:
            packet_type = random.choice(list(PACKET_TYPES.keys()))

        # Create packet
        packet = SimulatedPacket(packet_type)
        packet_count += 1

        # Convert to audio
        audio_signal, frequency = packet_to_audio(packet, profile, sample_rate)

        # Add to buffer
        audio_buffer = np.append(audio_buffer, audio_signal)

        # Print progress
        progress = min(100, int(len(audio_buffer) / sample_rate / duration * 100))
        print(f"\rProgress: {progress}% | Packets: {packet_count} | Current: {packet.type} | Size: {packet.size} bytes | Freq: {frequency:.1f} Hz", end="")

        # Wait a bit between packets based on pattern
        if pattern == "port_scan":
            time.sleep(0.01)  # Fast packets for port scan
        elif pattern == "data_transfer":
            time.sleep(0.05)  # Steady stream for data transfer
        else:
            time.sleep(random.uniform(0.02, 0.1))  # Random timing for other patterns

    # Trim to exact duration
    samples_needed = int(duration * sample_rate)
    if len(audio_buffer) > samples_needed:
        audio_buffer = audio_buffer[:samples_needed]

    # Normalize audio to prevent clipping
    max_amplitude = np.max(np.abs(audio_buffer))
    if max_amplitude > 0:
        audio_buffer = audio_buffer / max_amplitude * 0.9

    # Write to WAV file
    sf.write(output_file, audio_buffer, sample_rate)

    print(f"\nAudio sample exported to {output_file}")
    print(f"Duration: {duration} seconds")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Packets generated: {packet_count}")
    print(f"Generation time: {time.time() - start_time:.1f} seconds")

def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Export Network Audio Sample - Generate and export simulated network traffic audio"
    )
    parser.add_argument(
        "-o", "--output",
        default="network_audio_sample.wav",
        help="Output WAV file"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=30,
        help="Sample duration in seconds"
    )
    parser.add_argument(
        "-p", "--profile",
        choices=list(AUDIO_PROFILES.keys()),
        default="ambient",
        help="Audio profile to use"
    )
    parser.add_argument(
        "-t", "--pattern",
        choices=["random", "web_browsing", "port_scan", "data_transfer"],
        default="random",
        help="Traffic pattern to simulate"
    )
    parser.add_argument(
        "-s", "--sample-rate",
        type=int,
        default=44100,
        help="Audio sample rate in Hz"
    )

    args = parser.parse_args()

    export_audio_sample(
        args.output,
        args.duration,
        args.profile,
        args.pattern,
        args.sample_rate
    )

if __name__ == "__main__":
    main()
