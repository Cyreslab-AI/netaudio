#!/usr/bin/env python3
"""
Enhanced NetAudio Demo - Network Traffic Sonification

This script demonstrates the core functionality of NetAudio by sonifying network traffic
in real-time with improved visualization and feedback.
"""

import sys
import os
import time
import argparse
import threading
import curses
import random
import signal
from typing import Optional, Dict, List, Tuple
import numpy as np
import sounddevice as sd
from datetime import datetime

# Add parent directory to path to allow running script from examples directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netaudio.capture import LiveCapture, PacketData
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
    """Set up audio output stream.

    Args:
        sample_rate: Audio sample rate in Hz

    Returns:
        Audio output stream
    """
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

def generate_test_traffic(interface: str, intensity: str = "medium", duration: Optional[float] = None):
    """Generate test network traffic for demonstration purposes.

    Args:
        interface: Network interface to use
        intensity: Traffic intensity (low, medium, high)
        duration: Optional duration in seconds
    """
    try:
        from scapy.all import send, IP, TCP, UDP, ICMP, RandIP, RandTCPPort, RandUDPPort

        # Configure traffic parameters based on intensity
        if intensity == "low":
            packet_rate = 0.5  # packets per second
            protocols = ["TCP", "UDP", "ICMP"]
            weights = [0.7, 0.2, 0.1]  # Probability weights for each protocol
        elif intensity == "medium":
            packet_rate = 2.0
            protocols = ["TCP", "UDP", "ICMP"]
            weights = [0.6, 0.3, 0.1]
        else:  # high
            packet_rate = 5.0
            protocols = ["TCP", "UDP", "ICMP"]
            weights = [0.5, 0.4, 0.1]

        start_time = time.time()

        # Define packet generation functions
        def create_tcp_packet():
            return IP(dst="127.0.0.1") / TCP(
                sport=RandTCPPort(),
                dport=random.choice([80, 443, 8080, 22, 25, 3306]),
                flags=random.choice(["S", "A", "SA", "F", "FA", "R"])
            )

        def create_udp_packet():
            return IP(dst="127.0.0.1") / UDP(
                sport=RandUDPPort(),
                dport=random.choice([53, 123, 161, 5353, 1900])
            ) / ("X" * random.randint(10, 1000))

        def create_icmp_packet():
            return IP(dst="127.0.0.1") / ICMP(
                type=random.choice([0, 8, 3, 11])
            )

        packet_creators = {
            "TCP": create_tcp_packet,
            "UDP": create_udp_packet,
            "ICMP": create_icmp_packet
        }

        # Generate traffic until duration is reached
        while running:
            if duration and (time.time() - start_time) >= duration:
                break

            # Select protocol based on weights
            protocol = random.choices(protocols, weights=weights)[0]
            packet = packet_creators[protocol]()

            # Send packet
            send(packet, iface=interface, verbose=0)

            # Wait according to packet rate
            time.sleep(1.0 / packet_rate)

    except ImportError:
        print("Scapy is required for traffic generation. Install with: pip install scapy")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating test traffic: {e}")

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

def draw_ui(stdscr, packet_data: List[PacketData], audio_data: List[Dict], profile: str):
    """Draw the terminal UI using curses."""
    if not stdscr:
        return

    height, width = stdscr.getmaxyx()
    stdscr.clear()

    # Draw header
    header = f" NetAudio Demo - Profile: {profile.upper()} "
    stdscr.addstr(0, (width - len(header)) // 2, header, curses.color_pair(5) | curses.A_BOLD)

    # Draw instructions
    stdscr.addstr(1, 2, "Press 1-5 to change audio profile, 'q' to quit", curses.A_BOLD)
    stdscr.addstr(2, 2, "1: Ambient  2: Musical  3: Nature  4: Abstract  5: Alert", curses.A_BOLD)

    # Draw packet visualization
    stdscr.addstr(4, 2, "Recent Network Activity:", curses.A_BOLD)

    # Draw packet history (most recent first)
    for i, packet in enumerate(reversed(packet_data[-10:])):
        if i >= height - 8:  # Ensure we don't exceed terminal height
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

        stdscr.addstr(5 + i, 2, packet_info, color)

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

def handle_keyboard_input(mapper):
    """Handle keyboard input for profile switching."""
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
    except:
        pass  # Ignore curses errors

def signal_handler(sig, frame):
    """Handle interrupt signals."""
    global running
    running = False

def run_demo(interface: str, profile: str = "ambient",
             generate_traffic: bool = False, traffic_intensity: str = "medium",
             duration: Optional[float] = None, use_curses: bool = True):
    """Run the enhanced NetAudio demo.

    Args:
        interface: Network interface to monitor
        profile: Audio profile to use
        generate_traffic: Whether to generate test traffic
        traffic_intensity: Intensity of test traffic (low, medium, high)
        duration: Optional monitoring duration in seconds
        use_curses: Whether to use curses for terminal UI
    """
    global packet_history, audio_params_history, current_profile, running, stdscr

    # Initialize variables
    packet_history = []
    audio_params_history = []
    current_profile = profile
    running = True

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

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

    # Initialize UI if using curses
    if use_curses:
        try:
            stdscr = init_curses()
        except:
            use_curses = False
            print("Terminal doesn't support curses. Using simple output.")

    # Start test traffic generator if requested
    if generate_traffic:
        traffic_thread = threading.Thread(
            target=generate_test_traffic,
            args=(interface, traffic_intensity, duration),
            daemon=True
        )
        traffic_thread.start()
        print(f"Started test traffic generator with {traffic_intensity} intensity")

    # Print initial message if not using curses
    if not use_curses:
        print(f"Monitoring network traffic on interface {interface}...")
        print(f"Using {profile} audio profile")
        print("Press Ctrl+C to stop")

    start_time = time.time()
    try:
        with capture.stream() as packets:
            for packet in packets:
                if not running:
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

                # Handle keyboard input for profile switching
                handle_keyboard_input(mapper)

                # Update UI
                if use_curses:
                    draw_ui(stdscr, packet_history, audio_params_history, current_profile)
                else:
                    # Simple console output if not using curses
                    protocol = packet.protocol
                    size = packet.size
                    freq = audio_params.frequency
                    print(f"\r{protocol:4} | Size: {size:5} bytes | Freq: {freq:.1f} Hz | Profile: {current_profile}", end="")

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Clean up
        running = False
        if use_curses:
            cleanup_curses()
        audio_stream.stop()
        audio_stream.close()
        print("\nDemo stopped")

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced NetAudio Demo - Network Traffic Sonification"
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
    parser.add_argument(
        "-g", "--generate-traffic",
        action="store_true",
        help="Generate test traffic for demonstration"
    )
    parser.add_argument(
        "-t", "--traffic-intensity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Intensity of generated test traffic"
    )
    parser.add_argument(
        "--no-curses",
        action="store_true",
        help="Disable curses terminal UI"
    )

    args = parser.parse_args()

    # Check for root privileges if not generating traffic
    if os.geteuid() != 0 and not args.generate_traffic:
        print("Root privileges are required for network capture.")
        print("Please run with sudo or as root.")
        sys.exit(1)

    run_demo(
        interface=args.interface,
        profile=args.profile,
        generate_traffic=args.generate_traffic,
        traffic_intensity=args.traffic_intensity,
        duration=args.duration,
        use_curses=not args.no_curses
    )

if __name__ == "__main__":
    main()
