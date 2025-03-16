#!/usr/bin/env python3
"""
NetAudio PCAP Player

This script reads network packets from a PCAP file and sonifies them using
the NetAudio library, allowing for playback of recorded network traffic.
"""

import sys
import os
import time
import argparse
import curses
import threading
import signal
from typing import Optional, Dict, List
import numpy as np
import sounddevice as sd
from datetime import datetime

# Add parent directory to path to allow running script from examples directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netaudio.capture import PcapReader, PacketData
from netaudio.processors import FeatureExtractor, WindowProcessor, DataNormalizer, FeatureSet
from netaudio.audio import AudioMapper, Synthesizer
from netaudio.utils import ConfigManager

# Global variables for visualization
packet_history = []
audio_params_history = []
current_profile = "ambient"
running = True
stdscr = None  # For curses terminal UI

def setup_audio_stream(sample_rate: int = 44100) -> sd.OutputStream:
    """Set up audio output stream."""
    try:
        # Get default output device info
        default_output = sd.query_devices(kind='output')

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
        return stream
    except sd.PortAudioError as e:
        print(f"Error setting up audio: {e}")
        print("\nAvailable audio devices:")
        print(sd.query_devices())
        sys.exit(1)

def init_curses():
    """Initialize curses for terminal UI."""
    global stdscr
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.use_default_colors()
    stdscr.keypad(True)
    stdscr.nodelay(True)  # Non-blocking input

    # Initialize color pairs
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # TCP
    curses.init_pair(2, curses.COLOR_BLUE, -1)   # UDP
    curses.init_pair(3, curses.COLOR_RED, -1)    # ICMP
    curses.init_pair(4, curses.COLOR_YELLOW, -1) # Other
    curses.init_pair(5, curses.COLOR_CYAN, -1)   # Headers

    return stdscr

def cleanup_curses():
    """Clean up curses settings."""
    if stdscr:
        stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

def draw_ui(stdscr, packet_data: List[PacketData], audio_data: List[Dict], profile: str,
            pcap_file: str, speed: float, progress: float):
    """Draw the terminal UI using curses."""
    if not stdscr:
        return

    height, width = stdscr.getmaxyx()
    stdscr.clear()

    # Draw header
    header = f" NetAudio PCAP Player - Profile: {profile.upper()} "
    stdscr.addstr(0, (width - len(header)) // 2, header, curses.color_pair(5) | curses.A_BOLD)

    # Draw file info and controls
    stdscr.addstr(1, 2, f"File: {os.path.basename(pcap_file)}", curses.A_BOLD)
    stdscr.addstr(1, width - 20, f"Speed: {speed:.1f}x", curses.A_BOLD)

    # Draw progress bar
    progress_width = width - 20
    progress_pos = int(progress * progress_width)
    progress_bar = "█" * progress_pos + "░" * (progress_width - progress_pos)
    stdscr.addstr(2, 2, "Progress: ")
    stdscr.addstr(2, 12, progress_bar)
    stdscr.addstr(2, width - 8, f"{progress*100:.1f}%")

    # Draw instructions
    stdscr.addstr(3, 2, "Controls: 1-5: Change profile | +/-: Adjust speed | q: Quit", curses.A_BOLD)

    # Draw packet visualization
    stdscr.addstr(5, 2, "Recent Packets:", curses.A_BOLD)

    # Draw packet history (most recent first)
    for i, packet in enumerate(reversed(packet_data[-10:])):
        if i >= height - 12:  # Ensure we don't exceed terminal height
            break

        # Select color based on protocol
        if packet.protocol == "TCP":
            color = curses.color_pair(1)
        elif packet.protocol == "UDP":
            color = curses.color_pair(2)
        elif packet.protocol == "ICMP":
            color = curses.color_pair(3)
        else:
            color = curses.color_pair(4)

        # Format packet info
        timestamp = datetime.fromtimestamp(packet.timestamp).strftime("%H:%M:%S.%f")[:-3]
        if packet.src_port and packet.dst_port:
            packet_info = f"{timestamp} | {packet.protocol:4} | Size: {packet.size:5} bytes | {packet.src_port:5} → {packet.dst_port:5}"
        else:
            packet_info = f"{timestamp} | {packet.protocol:4} | Size: {packet.size:5} bytes"

        # Add flags for TCP
        if packet.protocol == "TCP" and packet.flags:
            flag_str = " | Flags: "
            if packet.flags.get("SYN"):
                flag_str += "SYN "
            if packet.flags.get("ACK"):
                flag_str += "ACK "
            if packet.flags.get("FIN"):
                flag_str += "FIN "
            if packet.flags.get("RST"):
                flag_str += "RST "
            if packet.flags.get("PSH"):
                flag_str += "PSH "
            packet_info += flag_str

        stdscr.addstr(6 + i, 2, packet_info, color)

    # Draw audio mapping visualization
    if audio_data:
        stdscr.addstr(height - 10, 2, "Audio Mapping:", curses.A_BOLD)

        latest = audio_data[-1]
        stdscr.addstr(height - 9, 2, f"Frequency: {latest.get('frequency', 0):.1f} Hz | "
                                    f"Amplitude: {latest.get('amplitude', 0):.2f} | "
                                    f"Waveform: {latest.get('waveform', 'sine')} | "
                                    f"Duration: {latest.get('duration', 0):.3f}s")

        # Draw simple visualization of frequency and amplitude
        bar_width = width - 10
        freq_normalized = min(1.0, latest.get('frequency', 440) / 2000)
        amp_normalized = latest.get('amplitude', 0.5)

        stdscr.addstr(height - 7, 2, "Frequency: ")
        stdscr.addstr(height - 7, 13, "█" * int(freq_normalized * bar_width))

        stdscr.addstr(height - 6, 2, "Amplitude: ")
        stdscr.addstr(height - 6, 13, "█" * int(amp_normalized * bar_width))

    # Draw footer with stats
    if packet_data:
        total_bytes = sum(p.size for p in packet_data[-100:])
        protocols = {}
        for p in packet_data[-100:]:
            protocols[p.protocol] = protocols.get(p.protocol, 0) + 1

        stats = f"Last 100 packets: {total_bytes} bytes | "
        for proto, count in protocols.items():
            stats += f"{proto}: {count} | "

        stdscr.addstr(height - 2, 2, stats.rstrip(" |"))

    stdscr.refresh()

def handle_keyboard_input(mapper, speed_ref):
    """Handle keyboard input for profile switching and speed control."""
    global current_profile, running, stdscr

    if not stdscr:
        return

    try:
        key = stdscr.getch()
        if key == ord('q'):
            running = False
        elif key == ord('1'):
            current_profile = "ambient"
            mapper.set_profile(current_profile)
        elif key == ord('2'):
            current_profile = "musical"
            mapper.set_profile(current_profile)
        elif key == ord('3'):
            current_profile = "nature"
            mapper.set_profile(current_profile)
        elif key == ord('4'):
            current_profile = "abstract"
            mapper.set_profile(current_profile)
        elif key == ord('5'):
            current_profile = "alert"
            mapper.set_profile(current_profile)
        elif key == ord('+') or key == ord('='):
            speed_ref[0] = min(10.0, speed_ref[0] + 0.1)
        elif key == ord('-') or key == ord('_'):
            speed_ref[0] = max(0.1, speed_ref[0] - 0.1)
    except:
        pass  # Ignore curses errors

def signal_handler(sig, frame):
    """Handle interrupt signals."""
    global running
    running = False

def play_pcap(pcap_file: str, profile: str = "ambient", speed: float = 1.0,
              loop: bool = False, use_curses: bool = True):
    """Play audio from a PCAP file.

    Args:
        pcap_file: Path to PCAP file
        profile: Audio profile to use
        speed: Playback speed multiplier
        loop: Whether to loop the PCAP file
        use_curses: Whether to use curses for terminal UI
    """
    global packet_history, audio_params_history, current_profile, running, stdscr

    # Initialize variables
    packet_history = []
    audio_params_history = []
    current_profile = profile
    running = True
    speed_ref = [speed]  # Use a list to allow modification in handle_keyboard_input

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Load configuration
    config = ConfigManager()

    # Set up audio output
    audio_stream = setup_audio_stream(config.audio.sample_rate)

    # Initialize components
    pcap_reader = PcapReader(filepath=pcap_file, loop=loop)
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

    # Initialize UI if using curses
    if use_curses:
        try:
            stdscr = init_curses()
        except:
            use_curses = False
            print("Terminal doesn't support curses. Using simple output.")

    # Print initial message if not using curses
    if not use_curses:
        print(f"Playing PCAP file: {pcap_file}")
        print(f"Using {profile} audio profile at {speed}x speed")
        print("Press Ctrl+C to stop")

    try:
        # Start the PCAP reader
        pcap_reader.start()

        # Get total packet count for progress calculation
        total_packets = pcap_reader._packet_count
        processed_packets = 0

        # Process packets
        while running:
            # Get next packet
            packet = pcap_reader.get_packet()

            if not packet:
                if loop:
                    # If looping, we should get more packets after a while
                    time.sleep(0.1)
                    continue
                else:
                    # End of file
                    break

            # Store packet for visualization
            packet_history.append(packet)
            if len(packet_history) > 1000:
                packet_history = packet_history[-1000:]

            # Extract and process features
            features = extractor.extract(packet)
            normalizer.update_stats(features)
            normalized_features = normalizer.normalize(features)

            # Generate audio
            audio_params = mapper.map_packet(normalized_features)

            # Store audio parameters for visualization
            audio_params_dict = {
                'frequency': audio_params.frequency,
                'amplitude': audio_params.amplitude,
                'waveform': audio_params.waveform,
                'duration': audio_params.duration
            }
            audio_params_history.append(audio_params_dict)
            if len(audio_params_history) > 100:
                audio_params_history = audio_params_history[-100:]

            # Generate and play audio
            audio_signal = synth.generate(audio_params)
            audio_signal = np.clip(audio_signal, -1.0, 1.0)
            audio_stream.write(audio_signal.astype(np.float32))

            # Calculate progress
            processed_packets += 1
            progress = processed_packets / total_packets if total_packets > 0 else 0

            # Handle keyboard input for profile switching and speed control
            handle_keyboard_input(mapper, speed_ref)

            # Update UI
            if use_curses:
                draw_ui(stdscr, packet_history, audio_params_history, current_profile,
                        pcap_file, speed_ref[0], progress)
            else:
                # Simple console output if not using curses
                protocol = packet.protocol
                size = packet.size
                freq = audio_params.frequency
                print(f"\r{protocol:4} | Size: {size:5} bytes | Freq: {freq:.1f} Hz | "
                      f"Profile: {current_profile} | Speed: {speed_ref[0]:.1f}x | "
                      f"Progress: {progress*100:.1f}%", end="")

            # Control playback speed
            if audio_params.duration > 0 and speed_ref[0] > 0:
                # Sleep for a fraction of the duration based on speed
                time.sleep(audio_params.duration / speed_ref[0])

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Clean up
        running = False
        if use_curses:
            cleanup_curses()
        pcap_reader.stop()
        audio_stream.stop()
        audio_stream.close()
        print("\nPlayback stopped")

def main():
    parser = argparse.ArgumentParser(
        description="NetAudio PCAP Player - Sonify network traffic from PCAP files"
    )
    parser.add_argument(
        "pcap_file",
        help="Path to PCAP file"
    )
    parser.add_argument(
        "-p", "--profile",
        choices=["ambient", "musical", "nature", "abstract", "alert"],
        default="ambient",
        help="Audio profile to use"
    )
    parser.add_argument(
        "-s", "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier"
    )
    parser.add_argument(
        "-l", "--loop",
        action="store_true",
        help="Loop the PCAP file"
    )
    parser.add_argument(
        "--no-curses",
        action="store_true",
        help="Disable curses terminal UI"
    )

    args = parser.parse_args()

    # Check if file exists
    if not os.path.isfile(args.pcap_file):
        print(f"Error: PCAP file not found: {args.pcap_file}")
        sys.exit(1)

    play_pcap(
        pcap_file=args.pcap_file,
        profile=args.profile,
        speed=args.speed,
        loop=args.loop,
        use_curses=not args.no_curses
    )

if __name__ == "__main__":
    main()
