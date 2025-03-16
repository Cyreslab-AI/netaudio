#!/usr/bin/env python3
"""
NetAudio Test Traffic Generator

This script generates test network traffic for demonstrating and testing
the NetAudio network sonification system.
"""

import sys
import os
import time
import argparse
import random
import threading
import signal
from typing import List, Dict, Optional, Tuple

# Add parent directory to path to allow running script from examples directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Global flag for controlling traffic generation
running = True

def signal_handler(sig, frame):
    """Handle interrupt signals."""
    global running
    running = False
    print("\nStopping traffic generation...")

def generate_basic_traffic(interface: str, intensity: str = "medium", duration: Optional[float] = None):
    """Generate basic test network traffic with mixed protocols.

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

        print(f"Generating {intensity} traffic on interface {interface}")
        print(f"Packet rate: {packet_rate} packets/second")
        print("Protocol distribution:")
        for p, w in zip(protocols, weights):
            print(f"  {p}: {w*100:.1f}%")

        start_time = time.time()
        packet_count = 0

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

        # Generate traffic until duration is reached or interrupted
        while running:
            if duration and (time.time() - start_time) >= duration:
                break

            # Select protocol based on weights
            protocol = random.choices(protocols, weights=weights)[0]
            packet = packet_creators[protocol]()

            # Send packet
            send(packet, iface=interface, verbose=0)
            packet_count += 1

            # Print status update
            elapsed = time.time() - start_time
            print(f"\rGenerated {packet_count} packets ({protocol}) in {elapsed:.1f} seconds", end="")

            # Wait according to packet rate
            time.sleep(1.0 / packet_rate)

        print(f"\nFinished generating {packet_count} packets in {time.time() - start_time:.1f} seconds")

    except ImportError:
        print("Scapy is required for traffic generation. Install with: pip install scapy")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating test traffic: {e}")

def generate_port_scan(interface: str, target_ip: str = "127.0.0.1", scan_type: str = "syn", duration: Optional[float] = None):
    """Generate port scan traffic.

    Args:
        interface: Network interface to use
        target_ip: Target IP address
        scan_type: Type of scan (syn, connect, fin)
        duration: Optional duration in seconds
    """
    try:
        from scapy.all import send, IP, TCP, sr1

        # Configure scan parameters
        if scan_type == "syn":
            flags = "S"
            packet_rate = 10.0  # packets per second
        elif scan_type == "fin":
            flags = "F"
            packet_rate = 8.0
        else:  # connect
            flags = "S"
            packet_rate = 5.0

        # Common ports to scan
        ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
                993, 995, 1723, 3306, 3389, 5900, 8080]

        print(f"Generating {scan_type} port scan on {target_ip} via {interface}")
        print(f"Scanning {len(ports)} ports at {packet_rate} packets/second")

        start_time = time.time()
        packet_count = 0

        # Generate port scan traffic
        while running:
            if duration and (time.time() - start_time) >= duration:
                break

            # Cycle through ports
            for port in ports:
                if not running or (duration and (time.time() - start_time) >= duration):
                    break

                # Create and send packet
                packet = IP(dst=target_ip) / TCP(dport=port, flags=flags)
                send(packet, iface=interface, verbose=0)
                packet_count += 1

                # Print status update
                elapsed = time.time() - start_time
                print(f"\rScanned {packet_count} ports in {elapsed:.1f} seconds (current: {port})", end="")

                # Wait according to packet rate
                time.sleep(1.0 / packet_rate)

        print(f"\nFinished port scan with {packet_count} packets in {time.time() - start_time:.1f} seconds")

    except ImportError:
        print("Scapy is required for traffic generation. Install with: pip install scapy")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating port scan traffic: {e}")

def generate_data_transfer(interface: str, size_mb: float = 1.0, protocol: str = "tcp", duration: Optional[float] = None):
    """Generate data transfer traffic.

    Args:
        interface: Network interface to use
        size_mb: Size of data to transfer in MB
        protocol: Protocol to use (tcp, udp)
        duration: Optional duration in seconds
    """
    try:
        from scapy.all import send, IP, TCP, UDP

        # Calculate packet parameters
        total_bytes = int(size_mb * 1024 * 1024)
        packet_size = 1400  # bytes per packet
        total_packets = total_bytes // packet_size

        if protocol.lower() == "tcp":
            packet_rate = 100.0  # packets per second
            dst_port = 80
        else:  # udp
            packet_rate = 200.0
            dst_port = 53

        print(f"Generating {size_mb} MB {protocol.upper()} data transfer on {interface}")
        print(f"Sending {total_packets} packets of {packet_size} bytes at {packet_rate} packets/second")

        start_time = time.time()
        packet_count = 0

        # Generate data transfer traffic
        while running and packet_count < total_packets:
            if duration and (time.time() - start_time) >= duration:
                break

            # Create packet batch
            batch_size = min(int(packet_rate), total_packets - packet_count)
            if batch_size <= 0:
                break

            for _ in range(batch_size):
                # Create and send packet
                if protocol.lower() == "tcp":
                    packet = IP(dst="127.0.0.1") / TCP(dport=dst_port) / ("X" * packet_size)
                else:
                    packet = IP(dst="127.0.0.1") / UDP(dport=dst_port) / ("X" * packet_size)

                send(packet, iface=interface, verbose=0)
                packet_count += 1

            # Print status update
            elapsed = time.time() - start_time
            mb_sent = (packet_count * packet_size) / (1024 * 1024)
            print(f"\rSent {packet_count}/{total_packets} packets ({mb_sent:.2f}/{size_mb:.2f} MB) in {elapsed:.1f} seconds", end="")

            # Wait according to packet rate
            time.sleep(batch_size / packet_rate)

        print(f"\nFinished data transfer with {packet_count} packets in {time.time() - start_time:.1f} seconds")

    except ImportError:
        print("Scapy is required for traffic generation. Install with: pip install scapy")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating data transfer traffic: {e}")

def generate_mixed_scenario(interface: str, scenario: str = "normal", duration: Optional[float] = None):
    """Generate mixed traffic scenario.

    Args:
        interface: Network interface to use
        scenario: Scenario type (normal, busy, attack)
        duration: Optional duration in seconds
    """
    try:
        from scapy.all import send, IP, TCP, UDP, ICMP

        # Configure scenario parameters
        if scenario == "normal":
            # Normal traffic: mostly web browsing, some DNS, occasional pings
            tcp_weight = 0.7
            udp_weight = 0.25
            icmp_weight = 0.05
            packet_rate = 3.0
        elif scenario == "busy":
            # Busy network: heavy web traffic, streaming, downloads
            tcp_weight = 0.8
            udp_weight = 0.15
            icmp_weight = 0.05
            packet_rate = 10.0
        else:  # attack
            # Attack scenario: port scan + normal traffic + some ICMP floods
            tcp_weight = 0.6
            udp_weight = 0.2
            icmp_weight = 0.2
            packet_rate = 15.0

        print(f"Generating '{scenario}' traffic scenario on {interface}")
        print(f"TCP: {tcp_weight*100:.1f}%, UDP: {udp_weight*100:.1f}%, ICMP: {icmp_weight*100:.1f}%")
        print(f"Packet rate: {packet_rate} packets/second")

        start_time = time.time()
        packet_count = 0
        protocol_counts = {"TCP": 0, "UDP": 0, "ICMP": 0}

        # TCP packet types for different scenarios
        if scenario == "normal":
            tcp_ports = [80, 443, 8080]
            tcp_flags = ["S", "A", "PA", "FA"]
            tcp_weights = [0.2, 0.4, 0.3, 0.1]
        elif scenario == "busy":
            tcp_ports = [80, 443, 8080, 22, 3389]
            tcp_flags = ["S", "A", "PA", "FA"]
            tcp_weights = [0.1, 0.5, 0.3, 0.1]
        else:  # attack
            tcp_ports = list(range(20, 100)) + [80, 443, 8080]
            tcp_flags = ["S", "A", "PA", "FA", "R"]
            tcp_weights = [0.5, 0.2, 0.1, 0.1, 0.1]

        # UDP packet types
        if scenario == "normal":
            udp_ports = [53, 123, 5353]
            udp_sizes = [64, 128, 256]
        elif scenario == "busy":
            udp_ports = [53, 123, 5353, 1900, 5004]
            udp_sizes = [64, 128, 256, 512, 1024]
        else:  # attack
            udp_ports = [53, 123, 5353, 1900, 5004, 111, 137]
            udp_sizes = [64, 128, 256, 512, 1024, 1400]

        # Generate traffic until duration is reached or interrupted
        while running:
            if duration and (time.time() - start_time) >= duration:
                break

            # Determine packet type
            packet_type = random.choices(
                ["TCP", "UDP", "ICMP"],
                weights=[tcp_weight, udp_weight, icmp_weight]
            )[0]

            # Create packet based on type and scenario
            if packet_type == "TCP":
                port = random.choice(tcp_ports)
                flag = random.choices(tcp_flags, weights=tcp_weights)[0]
                packet = IP(dst="127.0.0.1") / TCP(dport=port, flags=flag)
                protocol_counts["TCP"] += 1
            elif packet_type == "UDP":
                port = random.choice(udp_ports)
                size = random.choice(udp_sizes)
                packet = IP(dst="127.0.0.1") / UDP(dport=port) / ("X" * size)
                protocol_counts["UDP"] += 1
            else:  # ICMP
                if scenario == "attack" and random.random() < 0.7:
                    # ICMP flood in attack scenario
                    packet = IP(dst="127.0.0.1") / ICMP(type=8)
                else:
                    packet = IP(dst="127.0.0.1") / ICMP(type=random.choice([0, 8, 3, 11]))
                protocol_counts["ICMP"] += 1

            # Send packet
            send(packet, iface=interface, verbose=0)
            packet_count += 1

            # Print status update
            elapsed = time.time() - start_time
            stats = f"TCP: {protocol_counts['TCP']}, UDP: {protocol_counts['UDP']}, ICMP: {protocol_counts['ICMP']}"
            print(f"\rGenerated {packet_count} packets in {elapsed:.1f} seconds ({stats})", end="")

            # Wait according to packet rate
            time.sleep(1.0 / packet_rate)

        print(f"\nFinished generating {packet_count} packets in {time.time() - start_time:.1f} seconds")
        print(f"Protocol distribution: {stats}")

    except ImportError:
        print("Scapy is required for traffic generation. Install with: pip install scapy")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating scenario traffic: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="NetAudio Test Traffic Generator"
    )
    parser.add_argument(
        "-i", "--interface",
        required=True,
        help="Network interface to use"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["basic", "port-scan", "data-transfer", "scenario"],
        default="basic",
        help="Traffic generation mode"
    )
    parser.add_argument(
        "-d", "--duration",
        type=float,
        help="Duration in seconds"
    )

    # Basic mode options
    parser.add_argument(
        "--intensity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Traffic intensity for basic mode"
    )

    # Port scan options
    parser.add_argument(
        "--target",
        default="127.0.0.1",
        help="Target IP for port scan"
    )
    parser.add_argument(
        "--scan-type",
        choices=["syn", "connect", "fin"],
        default="syn",
        help="Port scan type"
    )

    # Data transfer options
    parser.add_argument(
        "--size",
        type=float,
        default=1.0,
        help="Size in MB for data transfer"
    )
    parser.add_argument(
        "--protocol",
        choices=["tcp", "udp"],
        default="tcp",
        help="Protocol for data transfer"
    )

    # Scenario options
    parser.add_argument(
        "--scenario",
        choices=["normal", "busy", "attack"],
        default="normal",
        help="Traffic scenario type"
    )

    args = parser.parse_args()

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Check for root privileges
    if os.geteuid() != 0:
        print("Root privileges are required for packet generation.")
        print("Please run with sudo or as root.")
        sys.exit(1)

    # Run selected traffic generation mode
    if args.mode == "basic":
        generate_basic_traffic(args.interface, args.intensity, args.duration)
    elif args.mode == "port-scan":
        generate_port_scan(args.interface, args.target, args.scan_type, args.duration)
    elif args.mode == "data-transfer":
        generate_data_transfer(args.interface, args.size, args.protocol, args.duration)
    elif args.mode == "scenario":
        generate_mixed_scenario(args.interface, args.scenario, args.duration)

if __name__ == "__main__":
    main()
