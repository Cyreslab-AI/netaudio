#!/bin/bash
# NetAudio Complete Demo Script
# This script demonstrates the key features of the NetAudio project

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo) for network capture capabilities"
  exit 1
fi

# Set variables
INTERFACE="lo0"  # Change to your network interface (e.g., eth0, en0, lo0)
DURATION=10      # Duration for each demo in seconds
PCAP_FILE="demo_capture.pcap"

# Print header
echo "=============================================="
echo "NetAudio - Network Traffic Sonification Demo"
echo "=============================================="
echo ""

# Function to wait for user input
wait_for_user() {
  echo ""
  read -p "Press Enter to continue..."
  echo ""
}

# Step 1: Capture some network traffic
echo "Step 1: Capturing network traffic to PCAP file"
echo "---------------------------------------------"
echo "Capturing $DURATION seconds of traffic on $INTERFACE..."
python examples/capture_to_pcap.py -i $INTERFACE -d $DURATION -o $PCAP_FILE
wait_for_user

# Step 2: Generate and sonify different types of test traffic
echo "Step 2: Generating and sonifying test traffic"
echo "---------------------------------------------"
echo "Starting basic traffic generation..."
echo "This will run for $DURATION seconds. Listen to the sounds!"
echo "Press Ctrl+C when you want to stop"
python examples/run_demo.py -i $INTERFACE -t basic -p ambient -d $DURATION
wait_for_user

echo "Starting port scan traffic generation..."
echo "This will run for $DURATION seconds. Notice the different sound pattern!"
python examples/run_demo.py -i $INTERFACE -t port-scan -p alert -d $DURATION
wait_for_user

echo "Starting data transfer traffic generation..."
echo "This will run for $DURATION seconds. Listen to the consistent pattern!"
python examples/run_demo.py -i $INTERFACE -t data-transfer -p musical -d $DURATION
wait_for_user

# Step 3: Play back the captured PCAP file with different profiles
echo "Step 3: Playing back captured PCAP file"
echo "---------------------------------------------"
echo "Playing back with ambient profile..."
echo "This will play the entire PCAP file. Press 'q' to stop early."
python examples/pcap_player.py $PCAP_FILE -p ambient
wait_for_user

echo "Playing back with musical profile at 2x speed..."
echo "This will play the entire PCAP file. Press 'q' to stop early."
python examples/pcap_player.py $PCAP_FILE -p musical -s 2.0
wait_for_user

# Step 4: Run the enhanced demo with visualization
echo "Step 4: Running enhanced demo with visualization"
echo "---------------------------------------------"
echo "Starting enhanced demo with test traffic generation..."
echo "This will run for $DURATION seconds."
echo "Use keys 1-5 to switch between audio profiles!"
python examples/enhanced_demo.py -i $INTERFACE -g -d $DURATION

# Clean up
echo ""
echo "Demo completed! PCAP file saved as $PCAP_FILE"
echo "You can play it back anytime with:"
echo "python examples/pcap_player.py $PCAP_FILE"
echo ""
echo "Thank you for trying NetAudio!"
