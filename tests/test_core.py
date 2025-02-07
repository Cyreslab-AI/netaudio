"""Core functionality tests."""

import pytest
import numpy as np
from netaudio.capture import PacketData
from netaudio.processors import FeatureExtractor, FeatureSet
from netaudio.audio import AudioMapper, AudioParameters, Synthesizer

@pytest.fixture
def sample_packet():
    """Create a sample packet for testing."""
    return PacketData(
        timestamp=1234567890.0,
        size=1500,
        protocol="TCP",
        src_port=80,
        dst_port=443,
        flags={"SYN": True, "ACK": False},
        payload=b"Test payload"
    )

@pytest.fixture
def feature_extractor():
    """Create a feature extractor instance."""
    return FeatureExtractor()

@pytest.fixture
def audio_mapper():
    """Create an audio mapper instance."""
    return AudioMapper()

@pytest.fixture
def synthesizer():
    """Create a synthesizer instance."""
    return Synthesizer(sample_rate=44100)

def test_packet_feature_extraction(sample_packet, feature_extractor):
    """Test feature extraction from a packet."""
    features = feature_extractor.extract(sample_packet)
    
    assert isinstance(features, FeatureSet)
    assert "packet_size" in features.features
    assert "protocol_type" in features.features
    assert "port_range" in features.features
    
    assert features.features["packet_size"] == float(sample_packet.size)
    assert 0 <= features.features["protocol_type"] <= 1
    assert 0 <= features.features["port_range"] <= 1

def test_audio_mapping(sample_packet, feature_extractor, audio_mapper):
    """Test mapping packet features to audio parameters."""
    features = feature_extractor.extract(sample_packet)
    audio_params = audio_mapper.map_packet(features)
    
    assert isinstance(audio_params, AudioParameters)
    assert 20 <= audio_params.frequency <= 20000  # Human hearing range
    assert 0 <= audio_params.amplitude <= 1
    assert audio_params.waveform in ["sine", "square", "sawtooth", "noise"]
    assert 0 < audio_params.duration <= 1

def test_audio_synthesis(synthesizer):
    """Test audio signal synthesis."""
    params = AudioParameters(
        frequency=440.0,  # A4 note
        amplitude=0.5,
        waveform="sine",
        duration=0.1,
        effects={}
    )
    
    signal = synthesizer.generate(params)
    
    assert isinstance(signal, np.ndarray)
    assert len(signal) == int(synthesizer.sample_rate * params.duration)
    assert -1 <= signal.min() <= 1
    assert -1 <= signal.max() <= 1

def test_waveform_types(synthesizer):
    """Test different waveform types."""
    duration = 0.1
    frequency = 440.0
    
    for waveform in ["sine", "square", "sawtooth", "noise"]:
        params = AudioParameters(
            frequency=frequency,
            amplitude=1.0,
            waveform=waveform,
            duration=duration,
            effects={}
        )
        
        signal = synthesizer.generate(params)
        assert len(signal) == int(synthesizer.sample_rate * duration)
        
        if waveform != "noise":
            # Check periodicity for deterministic waveforms
            period_samples = int(synthesizer.sample_rate / frequency)
            first_period = signal[:period_samples]
            second_period = signal[period_samples:2*period_samples]
            np.testing.assert_array_almost_equal(first_period, second_period, decimal=5)

def test_audio_effects(synthesizer):
    """Test audio effects processing."""
    params = AudioParameters(
        frequency=440.0,
        amplitude=0.5,
        waveform="sine",
        duration=0.1,
        effects={
            "reverb": {"delay": 0.01, "decay": 0.3},
            "filter": {"type": "lowpass", "cutoff": 1000, "order": 4}
        }
    )
    
    signal = synthesizer.generate(params)
    
    # Basic signal property checks
    assert isinstance(signal, np.ndarray)
    assert len(signal) == int(synthesizer.sample_rate * params.duration)
    assert -1 <= signal.min() <= 1
    assert -1 <= signal.max() <= 1

def test_invalid_parameters():
    """Test handling of invalid parameters."""
    synthesizer = Synthesizer()
    
    with pytest.raises(ValueError):
        # Test invalid waveform
        params = AudioParameters(
            frequency=440.0,
            amplitude=0.5,
            waveform="invalid",
            duration=0.1,
            effects={}
        )
        synthesizer.generate(params)
    
    with pytest.raises(ValueError):
        # Test invalid frequency
        params = AudioParameters(
            frequency=-100,
            amplitude=0.5,
            waveform="sine",
            duration=0.1,
            effects={}
        )
        synthesizer.generate(params)
