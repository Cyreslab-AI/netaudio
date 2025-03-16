#!/usr/bin/env python3
"""
NetAudio PCAP Capture

This script captures network traffic to a PCAP file, which can then be
played back using the pcap_player.py script.
"""

import sys
import os
import time
import argparse
import signal
from datetime import datetime

# Add parent directory to path to allow running script from examples directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Global flag for controlling capture
running = True

def signal_handler(sig, frame):
    """Handle interrupt signals."""
    global running
    running = False
    print("\nStopping capture...")

def capture_to_pcap(interface: str, output_file: str, duration: float = None,
                   filter_str: str = None, packet_count: int = None):
    """Capture network traffic to a PCAP file.

    Args:
        interface: Network interface to capture from
        output_file: Path to output PCAP file
        duration: Optional duration in seconds
        filter_str: Optional BPF filter string
        packet_count: Optional maximum number of packets to capture
    """
    try:
        from scapy.all import sniff, wrpcap
        import os

        # Ensure we have root privileges for capture
        if os.geteuid() != 0:
            print("Root privileges are required for network capture.")
            print("Please run with sudo or as root.")
            sys.exit(1)

        # Set up signal handler
        signal.signal(signal.SIGINT, signal_handler)

        # Prepare capture parameters
        kwargs = {
            'iface': interface,
            'store': True,
            'prn': lambda x: packet_callback(x),
        }

        if filter_str:
            kwargs['filter'] = filter_str

        if packet_count:
            kwargs['count'] = packet_count

        # Start capture
        print(f"Starting capture on interface {interface}")
        if filter_str:
            print(f"Filter: {filter_str}")
        if duration:
            print(f"Duration: {duration} seconds")
        if packet_count:
            print(f"Maximum packets: {packet_count}")
        print(f"Output file: {output_file}")
        print("Press Ctrl+C to stop capture")

        start_time = time.time()
        captured_packets = []

        # Define packet callback
        def packet_callback(packet):
            global running

            # Check if we've reached the duration limit
            if duration and (time.time() - start_time) >= duration:
                running = False
                return

            # Store packet
            captured_packets.append(packet)

            # Print status
            print(f"\rCaptured {len(captured_packets)} packets", end="")

            return running

        # Start capture
        packets = sniff(**kwargs)

        # If we got here through count limit or manual stop
        if not packets and captured_packets:
            packets = captured_packets

        # Write packets to PCAP file
        if packets:
            wrpcap(output_file, packets)
            print(f"\nWrote {len(packets)} packets to {output_file}")
        else:
            print("\nNo packets captured")

    except ImportError:
        print("Scapy is required for packet capture. Install with: pip install scapy")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="NetAudio PCAP Capture - Capture network traffic to a PCAP file"
    )
    parser.add_argument(
        "-i", "--interface",
        required=True,
        help="Network interface to capture from"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output PCAP file (default: capture_YYYYMMDD_HHMMSS.pcap)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=float,
        help="Capture duration in seconds"
    )
    parser.add_argument(
        "-f", "--filter",
        help="BPF filter string (e.g., 'tcp port 80' or 'udp')"
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        help="Maximum number of packets to capture"
    )

    args = parser.parse_args()

    # Generate default output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"capture_{timestamp}.pcap"

    capture_to_pcap(
        interface=args.interface,
        output_file=args.output,
        duration=args.duration,
        filter_str=args.filter,
        packet_count=args.count
    )

if __name__ == "__main__":
    main()
