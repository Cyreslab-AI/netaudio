#!/usr/bin/env python3
"""
NetAudio Demo Runner

This script provides a simple way to run a complete NetAudio demonstration,
combining the enhanced demo with test traffic generation.
"""

import sys
import os
import time
import argparse
import threading
import subprocess
import signal
from typing import Optional

# Add parent directory to path to allow running script from examples directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_demo(interface: str, profile: str = "ambient",
             traffic_mode: str = "basic", traffic_intensity: str = "medium",
             scenario: str = "normal", duration: Optional[float] = None):
    """Run a complete NetAudio demonstration.

    Args:
        interface: Network interface to use
        profile: Audio profile to use
        traffic_mode: Traffic generation mode
        traffic_intensity: Traffic intensity
        scenario: Traffic scenario type
        duration: Optional duration in seconds
    """
    # Determine if we need root privileges
    needs_root = os.geteuid() != 0

    if needs_root:
        print("Root privileges are required for network capture.")
        print("Please run with sudo or as root.")
        sys.exit(1)

    # Build command for enhanced demo
    demo_cmd = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "enhanced_demo.py"),
        "-i", interface,
        "-p", profile
    ]

    if duration:
        demo_cmd.extend(["-d", str(duration)])

    # Build command for traffic generator
    if traffic_mode == "basic":
        traffic_cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "test_traffic_generator.py"),
            "-i", interface,
            "-m", "basic",
            "--intensity", traffic_intensity
        ]
    elif traffic_mode == "port-scan":
        traffic_cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "test_traffic_generator.py"),
            "-i", interface,
            "-m", "port-scan",
            "--target", "127.0.0.1",
            "--scan-type", "syn"
        ]
    elif traffic_mode == "data-transfer":
        traffic_cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "test_traffic_generator.py"),
            "-i", interface,
            "-m", "data-transfer",
            "--size", "1.0",
            "--protocol", "tcp"
        ]
    else:  # scenario
        traffic_cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "test_traffic_generator.py"),
            "-i", interface,
            "-m", "scenario",
            "--scenario", scenario
        ]

    if duration:
        traffic_cmd.extend(["-d", str(duration)])

    # Print demo information
    print("=" * 60)
    print("NetAudio Demo")
    print("=" * 60)
    print(f"Interface: {interface}")
    print(f"Audio Profile: {profile}")
    print(f"Traffic Mode: {traffic_mode}")
    if traffic_mode == "basic":
        print(f"Traffic Intensity: {traffic_intensity}")
    elif traffic_mode == "scenario":
        print(f"Traffic Scenario: {scenario}")
    if duration:
        print(f"Duration: {duration} seconds")
    print("=" * 60)
    print("Starting traffic generator...")

    # Start traffic generator in a separate process
    traffic_process = subprocess.Popen(traffic_cmd)

    # Give the traffic generator a moment to start
    time.sleep(1)

    print("Starting enhanced demo...")
    print("=" * 60)

    # Start enhanced demo
    demo_process = subprocess.Popen(demo_cmd)

    # Wait for processes to complete
    try:
        demo_process.wait()
    except KeyboardInterrupt:
        print("\nStopping demo...")
    finally:
        # Ensure both processes are terminated
        if traffic_process.poll() is None:
            traffic_process.terminate()
        if demo_process.poll() is None:
            demo_process.terminate()

    print("Demo completed.")

def main():
    parser = argparse.ArgumentParser(
        description="NetAudio Demo Runner"
    )
    parser.add_argument(
        "-i", "--interface",
        required=True,
        help="Network interface to use"
    )
    parser.add_argument(
        "-p", "--profile",
        choices=["ambient", "musical", "nature", "abstract", "alert"],
        default="ambient",
        help="Audio profile to use"
    )
    parser.add_argument(
        "-t", "--traffic-mode",
        choices=["basic", "port-scan", "data-transfer", "scenario"],
        default="basic",
        help="Traffic generation mode"
    )
    parser.add_argument(
        "--intensity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Traffic intensity for basic mode"
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "busy", "attack"],
        default="normal",
        help="Traffic scenario type"
    )
    parser.add_argument(
        "-d", "--duration",
        type=float,
        help="Duration in seconds"
    )

    args = parser.parse_args()

    run_demo(
        interface=args.interface,
        profile=args.profile,
        traffic_mode=args.traffic_mode,
        traffic_intensity=args.intensity,
        scenario=args.scenario,
        duration=args.duration
    )

if __name__ == "__main__":
    main()
