#!/usr/bin/env python3
"""Real-time network traffic monitoring example."""

import sys
import os
import time
import argparse
import termios
import tty
from typing import Optional
import sounddevice as sd
import numpy as np

from netaudio.capture import LiveCapture
from netaudio.processors import FeatureExtractor, WindowProcessor, DataNormalizer
from netaudio.audio import AudioMapper, Synthesizer
from netaudio.utils import ConfigManager

def setup_audio_stream(sample_rate: int = 44100) -> sd.OutputStream:
    """Set up audio output stream.
    
    Args:
        sample_rate: Audio sample rate in Hz
        
    Returns:
        Audio output stream
    """
    try:
        # Get default output device info
        devices = sd.query_devices()
        default_output = sd.query_devices(kind='output')
        print(f"Using audio device: {default_output['name']}")
        print(f"Device capabilities: {default_output}")
        
        # Configure stream with explicit device and blocksize
        stream = sd.OutputStream(
            device=default_output['index'],
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32,
            blocksize=1024,
            latency='low',
            callback=None  # Use blocking write mode
        )
        stream.start()
        print("Audio stream started successfully")
        return stream
    except sd.PortAudioError as e:
        print(f"Error setting up audio: {e}")
        print("\nAvailable audio devices:")
        print(sd.query_devices())
        sys.exit(1)

def setup_audio_permissions():
    """Set up audio permissions while maintaining capture privileges."""
    if os.geteuid() == 0:  # If we're root
        # Get SUDO_UID and SUDO_GID from environment
        sudo_uid = int(os.environ.get('SUDO_UID', 0))
        sudo_gid = int(os.environ.get('SUDO_GID', 0))
        
        if sudo_uid and sudo_gid:
            # Create audio stream with original user permissions
            os.setegid(sudo_gid)
            os.seteuid(sudo_uid)
            stream = setup_audio_stream(44100)
            # Restore root privileges for capture
            os.seteuid(0)
            os.setegid(0)
            return stream
    return setup_audio_stream(44100)

def monitor_network(interface: str, profile: str = "ambient", duration: Optional[float] = None):
    """Monitor network traffic and generate audio in real-time.
    
    Args:
        interface: Network interface to monitor
        profile: Audio profile to use (ambient, musical, nature, abstract, alert)
        duration: Optional monitoring duration in seconds
    """
    # Load configuration
    config = ConfigManager()
    
    # Set up audio output with proper permissions
    audio_stream = setup_audio_permissions()
    
    # Initialize components
    capture = LiveCapture(interface=interface)
    extractor = FeatureExtractor()
    window_proc = WindowProcessor(
        window_size=config.processing.window_size,
        overlap=config.processing.window_overlap
    )
    normalizer = DataNormalizer(config.processing.feature_ranges)
    mapper = AudioMapper()
    synth = Synthesizer(sample_rate=config.audio.sample_rate)
    
    # Set audio profile
    mapper.set_profile(profile)
    
    
    print(f"Monitoring network traffic on interface {interface}...")
    print(f"Using {profile} audio profile")
    print("Available commands:")
    print("  1-5: Switch audio profile")
    print("    1: Ambient (gentle, atmospheric)")
    print("    2: Musical (harmonious, melodic)")
    print("    3: Nature (organic, flowing)")
    print("    4: Abstract (minimal, clean)")
    print("    5: Alert (technical, detailed)")
    print("  Ctrl+C: Stop monitoring")
    
    # Profile mapping for keyboard input
    profile_map = {
        "1": "ambient",
        "2": "musical",
        "3": "nature",
        "4": "abstract",
        "5": "alert"
    }
    
    start_time = time.time()
    try:
        import threading

        def get_key_windows():
            """Get keypress for Windows systems."""
            import msvcrt
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode()
                    if key in profile_map:
                        new_profile = profile_map[key]
                        mapper.set_profile(new_profile)
                        print(f"\nSwitched to {new_profile} profile")

        def get_key_unix():
            """Get keypress for Unix-like systems."""
            old_settings = termios.tcgetattr(sys.stdin.fileno())
            try:
                tty.setraw(sys.stdin.fileno())
                while True:
                    key = sys.stdin.read(1)
                    if key in profile_map:
                        new_profile = profile_map[key]
                        mapper.set_profile(new_profile)
                        print(f"\nSwitched to {new_profile} profile")
                    elif key == '\x03':  # Ctrl+C
                        raise KeyboardInterrupt
            finally:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)

        # Start input handling thread based on OS
        if os.name == 'nt':
            input_thread = threading.Thread(target=get_key_windows, daemon=True)
        else:
            input_thread = threading.Thread(target=get_key_unix, daemon=True)
        input_thread.start()
        
        with capture.stream() as packets:
            for packet in packets:
                # Extract and process features
                features = extractor.extract(packet)
                normalizer.update_stats(features)
                normalized_features = normalizer.normalize(features)
                
                # Generate audio
                audio_params = mapper.map_packet(normalized_features)
                audio_signal = synth.generate(audio_params)
                
                # Play audio with debug info
                try:
                    # Ensure signal is in valid range
                    audio_signal = np.clip(audio_signal, -1.0, 1.0)
                    # Print signal stats
                    if len(audio_signal) > 0:
                        print(f"\rAudio signal - Min: {audio_signal.min():.2f}, Max: {audio_signal.max():.2f}, Mean: {audio_signal.mean():.2f}", end="")
                    audio_stream.write(audio_signal.astype(np.float32))
                except Exception as e:
                    print(f"\nError playing audio: {e}")
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break
                    
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        audio_stream.stop()
        audio_stream.close()

def main():
    parser = argparse.ArgumentParser(
        description="Monitor network traffic and generate audio in real-time"
    )
    parser.add_argument(
        "-i", "--interface",
        required=True,
        help="Network interface to monitor"
    )
    parser.add_argument(
        "-p", "--profile",
        choices=["ambient", "musical", "nature", "abstract", "alert"],
        default="ambient",
        help="Audio profile to use"
    )
    parser.add_argument(
        "-d", "--duration",
        type=float,
        help="Monitoring duration in seconds"
    )
    
    args = parser.parse_args()
    monitor_network(args.interface, args.profile, args.duration)

if __name__ == "__main__":
    main()
