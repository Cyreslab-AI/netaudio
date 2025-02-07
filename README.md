# NetAudio

Transform network traffic into audio signals for monitoring and analysis.

## Features

- Multiple input sources support (PCAP, live capture, NetFlow)
- Flexible network-to-audio mapping system
- Real-time and batch processing capabilities
- Extensible audio synthesis engine
- Future-ready for ML-based anomaly detection

## Installation

```bash
pip install netaudio
```

For development installation:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from netaudio.capture import LiveCapture
from netaudio.audio import AudioMapper, Synthesizer

# Initialize live capture
capture = LiveCapture(interface="eth0")

# Create audio mapper with default settings
mapper = AudioMapper()

# Initialize synthesizer
synth = Synthesizer(sample_rate=44100)

# Start real-time processing
with capture.stream() as packets:
    for packet in packets:
        # Extract features and map to audio parameters
        audio_params = mapper.map_packet(packet)
        
        # Generate audio
        audio_signal = synth.generate(audio_params)
        
        # Play or save the audio
        synth.play(audio_signal)
```

## Advanced Usage

### Custom Feature Mapping

```python
from netaudio.processors import FeatureExtractor
from netaudio.audio import CustomMapper

# Define custom feature extraction
extractor = FeatureExtractor()
extractor.add_feature("packet_size", lambda p: len(p))
extractor.add_feature("protocol", lambda p: p.proto)

# Create custom audio mapping
mapper = CustomMapper()
mapper.map_feature("packet_size", "frequency", range=(20, 2000))
mapper.map_feature("protocol", "amplitude", range=(0.1, 1.0))
```

### Batch Processing

```python
from netaudio.capture import PcapReader
from netaudio.audio import BatchProcessor

# Process PCAP file
reader = PcapReader("traffic.pcap")
processor = BatchProcessor(window_size=1000)  # 1 second windows

# Generate audio file
processor.process_file(reader, "output.wav")
```

## Architecture

The library is built with modularity and extensibility in mind:

- `capture/`: Network traffic capture modules
- `processors/`: Feature extraction and data transformation
- `audio/`: Audio synthesis and mapping
- `utils/`: Helper utilities and configuration

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
