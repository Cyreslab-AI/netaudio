# NetAudio: Network Traffic Sonification

NetAudio is a Python library for sonifying network traffic - converting network packet data into audio. This creates an auditory representation of network activity that can be used for monitoring or analysis purposes.

## Overview

NetAudio simulates network traffic patterns and converts them to audio, mapping packet characteristics to sound parameters. Different types of network traffic produce different sounds, allowing for intuitive monitoring and analysis of network activity.

### Key Features

- Real-time network traffic sonification
- Multiple audio profiles for different sonification styles
- Simulated network traffic patterns (port scan, data transfer, web browsing)
- Audio synthesis with different waveforms and effects
- Export audio samples to WAV files

## Installation

### Prerequisites

- Python 3.7+
- Root/sudo privileges (required for network packet capture)

### Option 1: Install from Source

Clone the repository and install the package:

```bash
git clone https://github.com/example/netaudio.git
cd netaudio
pip install -e .
```

This will install the package in development mode, along with all dependencies, and create command-line entry points for the example scripts.

### Option 2: Install from Requirements File

Install dependencies using the requirements.txt file:

```bash
pip install -r requirements.txt
```

### Option 3: Install Dependencies Manually

If you prefer, you can install the dependencies individually:

```bash
pip install numpy scipy sounddevice scapy
```

### Command-Line Tools

When installed via pip, the following command-line tools are available:

- `netaudio-demo`: Run the enhanced demo
- `netaudio-traffic`: Generate test traffic
- `netaudio-pcap`: Play back PCAP files
- `netaudio-capture`: Capture network traffic to PCAP files
- `netaudio-run`: Run the all-in-one demo runner

## Enhanced Demo

The enhanced demo provides a comprehensive demonstration of NetAudio's capabilities with improved visualization and feedback.

### Running the Demo

```bash
# Basic usage
sudo python examples/enhanced_demo.py -i <interface>

# With test traffic generation (no need for sudo)
python examples/enhanced_demo.py -i lo0 -g

# With specific audio profile
sudo python examples/enhanced_demo.py -i <interface> -p musical

# With time limit
sudo python examples/enhanced_demo.py -i <interface> -d 60  # Run for 60 seconds
```

### Command Line Options

- `-i, --interface`: Network interface to monitor (required)
- `-p, --profile`: Audio profile to use (ambient, musical, nature, abstract, alert)
- `-d, --duration`: Monitoring duration in seconds
- `-g, --generate-traffic`: Generate test traffic for demonstration
- `-t, --traffic-intensity`: Intensity of generated test traffic (low, medium, high)
- `--no-curses`: Disable curses terminal UI

### Interactive Controls

During the demo, you can use the following keyboard controls:

- `1-5`: Switch between audio profiles
  - `1`: Ambient (gentle, atmospheric)
  - `2`: Musical (harmonious, melodic)
  - `3`: Nature (organic, flowing)
  - `4`: Abstract (minimal, clean)
  - `5`: Alert (technical, detailed)
- `q`: Quit the demo
- `Ctrl+C`: Stop the demo

## Test Traffic Generator

The test traffic generator creates controlled network traffic for testing and demonstrating NetAudio without relying on actual network activity.

### Running the Traffic Generator

```bash
# Basic usage
sudo python examples/test_traffic_generator.py -i <interface>

# Generate port scan traffic
sudo python examples/test_traffic_generator.py -i <interface> -m port-scan

# Generate data transfer traffic
sudo python examples/test_traffic_generator.py -i <interface> -m data-transfer --size 5 --protocol tcp

# Generate scenario-based traffic
sudo python examples/test_traffic_generator.py -i <interface> -m scenario --scenario busy
```

### Command Line Options

- `-i, --interface`: Network interface to use (required)
- `-m, --mode`: Traffic generation mode (basic, port-scan, data-transfer, scenario)
- `-d, --duration`: Duration in seconds

#### Basic Mode Options

- `--intensity`: Traffic intensity (low, medium, high)

#### Port Scan Options

- `--target`: Target IP for port scan
- `--scan-type`: Port scan type (syn, connect, fin)

#### Data Transfer Options

- `--size`: Size in MB for data transfer
- `--protocol`: Protocol for data transfer (tcp, udp)

#### Scenario Options

- `--scenario`: Traffic scenario type (normal, busy, attack)

## Example Use Cases

### 1. Basic Network Monitoring

```bash
sudo python examples/enhanced_demo.py -i eth0
```

This will monitor actual network traffic on the eth0 interface and convert it to audio using the default ambient profile.

### 2. Demo with Generated Traffic

```bash
python examples/enhanced_demo.py -i lo0 -g -t medium
```

This will generate medium-intensity test traffic on the loopback interface and sonify it. This is useful for demonstrations without needing actual network traffic.

### 3. Simulating Attack Detection

```bash
# In one terminal
sudo python examples/enhanced_demo.py -i lo0 -p alert

# In another terminal
sudo python examples/test_traffic_generator.py -i lo0 -m scenario --scenario attack
```

This simulates an attack scenario with port scans and unusual traffic patterns, using the alert profile for more pronounced audio feedback.

### 4. Comparing Audio Profiles

```bash
python examples/enhanced_demo.py -i lo0 -g
```

Run the demo with generated traffic and use the number keys (1-5) to switch between different audio profiles to hear how they represent the same network traffic differently.

### 5. Using the All-in-One Demo Runner

```bash
sudo python examples/run_demo.py -i lo0 -t scenario --scenario busy -p musical
```

This uses the demo runner script to start both the traffic generator and the enhanced demo in a single command, making it easier to run demonstrations.

### 6. Playing Back PCAP Files

```bash
python examples/pcap_player.py path/to/capture.pcap -p nature -s 2.0
```

This plays back network traffic from a previously captured PCAP file, converting it to audio using the nature profile at 2x speed. This is useful for analyzing captured traffic or creating consistent demonstrations.

### 7. Complete Capture and Analysis Workflow

```bash
# Step 1: Capture network traffic to a PCAP file
sudo python examples/capture_to_pcap.py -i eth0 -d 60 -f "tcp" -o capture.pcap

# Step 2: Play back the captured traffic with audio
python examples/pcap_player.py capture.pcap -p musical

# Step 3: Compare with different audio profiles
python examples/pcap_player.py capture.pcap -p alert -s 2.0
```

This workflow demonstrates the complete process of capturing network traffic to a PCAP file and then analyzing it through audio. This approach allows for:

- Consistent demonstrations using the same traffic patterns
- Offline analysis of network traffic
- Comparison of different audio profiles on identical traffic
- Sharing captured traffic with others for collaborative analysis

### 8. Running the Complete Demo Script

For a guided tour of all NetAudio features, run the demo script:

```bash
sudo ./demo.sh
```

This script will:

1. Capture network traffic to a PCAP file
2. Generate and sonify different types of test traffic
3. Play back the captured PCAP file with different audio profiles
4. Run the enhanced demo with visualization

The script pauses between each step, allowing you to experience and understand each feature. It's perfect for demonstrations or getting familiar with the project's capabilities.

You can customize the script by editing the variables at the top:

- `INTERFACE`: Network interface to use (default: lo0)
- `DURATION`: Duration for each demo in seconds (default: 10)
- `PCAP_FILE`: Name of the PCAP file to create (default: demo_capture.pcap)

## Audio Profiles

NetAudio includes five different audio profiles, each with unique characteristics:

1. **Ambient**: Gentle, atmospheric sounds with low frequencies and reverb
2. **Musical**: Harmonious, scale-based sounds using a pentatonic scale
3. **Nature**: Natural sound approximations with bandpass filtering
4. **Abstract**: Clean, minimal sounds with high-pass filtering
5. **Alert**: Technical, detailed sounds with compression

## Troubleshooting

### Permission Issues

If you encounter permission errors when capturing packets:

```
Error: Root privileges required for network capture
```

Run the script with sudo or as root:

```bash
sudo python examples/enhanced_demo.py -i <interface>
```

Note: When using the `-g` (generate traffic) option, root privileges are not required as the traffic is generated locally.

### Audio Issues

If you encounter audio playback issues:

```
Error setting up audio: [Errno -9996] Device unavailable
```

Check your audio devices:

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Scapy Installation Issues

If you have trouble installing or using Scapy:

```
ImportError: Scapy is required for live capture
```

Try installing with:

```bash
pip install scapy
```

On some systems, you may need additional dependencies:

```bash
# For Debian/Ubuntu
sudo apt-get install python3-dev libpcap-dev
```

## Simulated Network Audio

The simulated network audio scripts provide a way to experience network traffic sonification without requiring actual network capture or root privileges. These scripts generate synthetic network packet data and convert it to audio.

### Real-time Simulation

The `simulated_network_audio.py` script plays simulated network traffic audio in real-time:

```bash
# Basic usage
python simulated_network_audio.py

# With specific profile and pattern
python simulated_network_audio.py -p musical -t port_scan

# With custom duration
python simulated_network_audio.py -d 60  # Run for 60 seconds
```

### Command Line Options

- `-d, --duration`: Simulation duration in seconds (default: 30)
- `-p, --profile`: Audio profile to use (ambient, musical, alert)
- `-t, --pattern`: Traffic pattern to simulate (random, web_browsing, port_scan, data_transfer)

### Export Audio Samples

The `export_audio_sample.py` script exports simulated network traffic audio to WAV files:

```bash
# Basic usage
python export_audio_sample.py -o output.wav

# With specific profile and pattern
python export_audio_sample.py -o port_scan.wav -p alert -t port_scan

# With custom duration and sample rate
python export_audio_sample.py -o high_quality.wav -d 60 -s 48000
```

### Command Line Options

- `-o, --output`: Output WAV file (default: network_audio_sample.wav)
- `-d, --duration`: Sample duration in seconds (default: 30)
- `-p, --profile`: Audio profile to use (ambient, musical, alert)
- `-t, --pattern`: Traffic pattern to simulate (random, web_browsing, port_scan, data_transfer)
- `-s, --sample-rate`: Audio sample rate in Hz (default: 44100)

## Project Structure

- `netaudio/`: Main package
  - `audio/`: Audio synthesis and mapping
  - `capture/`: Network packet capture (with support for live capture and PCAP files)
  - `processors/`: Feature extraction and processing
  - `utils/`: Utility functions and configuration
- `examples/`: Example scripts
  - `enhanced_demo.py`: Enhanced demo with visualization and test traffic generation
  - `test_traffic_generator.py`: Test traffic generator with various modes
  - `run_demo.py`: All-in-one demo runner
  - `pcap_player.py`: PCAP file player for offline analysis
  - `capture_to_pcap.py`: Utility to capture network traffic to PCAP files
  - `realtime_monitor.py`: Original real-time monitor
- `simulated_network_audio.py`: Real-time simulated network traffic sonification
- `export_audio_sample.py`: Export simulated network traffic audio to WAV files
- `README.md`: Documentation and usage examples

## License

This project is open source and available under the MIT License.
