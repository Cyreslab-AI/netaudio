"""Audio synthesis and mapping module."""

from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
from dataclasses import dataclass
from ..processors import FeatureSet
from .profiles import AudioProfile, AudioProfileManager

@dataclass
class AudioParameters:
    """Container for audio synthesis parameters."""
    frequency: float  # Base frequency in Hz
    amplitude: float  # Amplitude (0.0 to 1.0)
    waveform: str    # Waveform type (sine, square, sawtooth, noise)
    duration: float  # Duration in seconds
    effects: Dict[str, Any]  # Audio effects parameters
    profile: Optional[str] = None  # Audio profile name

class Synthesizer:
    """Audio signal synthesizer."""
    
    def __init__(self, sample_rate: int = 44100):
        """Initialize synthesizer.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        self._supported_waveforms = {
            "sine": self._generate_sine,
            "square": self._generate_square,
            "sawtooth": self._generate_sawtooth,
            "noise": self._generate_noise,
            "filtered_noise": self._generate_filtered_noise,
            "triangle": self._generate_triangle
        }
        self.profile_manager = AudioProfileManager()

    def generate(self, params: AudioParameters) -> np.ndarray:
        """Generate audio signal from parameters.
        
        Args:
            params: Audio parameters
            
        Returns:
            Audio signal as numpy array
        """
        # Get active profile
        profile = None
        if params.profile:
            profile = self.profile_manager.get_profile(params.profile)
        else:
            profile = self.profile_manager.get_current_profile()

        # Apply profile frequency constraints
        frequency = np.clip(
            params.frequency,
            profile.frequency_range[0],
            profile.frequency_range[1]
        )

        # Quantize to musical scale if available
        frequency = self.profile_manager.quantize_to_scale(frequency, profile)

        # Select waveform from profile's allowed waveforms
        waveform = params.waveform
        if waveform not in profile.waveforms:
            waveform = profile.waveforms[0]

        if waveform not in self._supported_waveforms:
            raise ValueError(f"Unsupported waveform: {waveform}")

        # Generate base waveform
        generator = self._supported_waveforms[waveform]
        signal = generator(frequency, params.duration)

        # Apply amplitude with profile scaling
        amplitude = params.amplitude * profile.scaling.get('amplitude', 1.0)
        signal *= amplitude

        # Apply profile effects
        signal = self.profile_manager.apply_profile(signal, profile)

        return signal

    def _generate_sine(self, frequency: float, duration: float) -> np.ndarray:
        """Generate sine wave."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return np.sin(2 * np.pi * frequency * t)

    def _generate_square(self, frequency: float, duration: float) -> np.ndarray:
        """Generate square wave."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return np.sign(np.sin(2 * np.pi * frequency * t))

    def _generate_sawtooth(self, frequency: float, duration: float) -> np.ndarray:
        """Generate sawtooth wave."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return 2 * (t * frequency - np.floor(0.5 + t * frequency))

    def _generate_noise(self, frequency: float, duration: float) -> np.ndarray:
        """Generate white noise."""
        samples = int(self.sample_rate * duration)
        return np.random.normal(0, 1, samples)

    def _generate_filtered_noise(self, frequency: float, duration: float) -> np.ndarray:
        """Generate filtered noise."""
        noise = self._generate_noise(frequency, duration)
        
        if frequency > 0:
            from scipy import signal
            nyquist = self.sample_rate / 2
            cutoff = min(frequency, nyquist)
            b, a = signal.butter(4, cutoff/nyquist)
            noise = signal.filtfilt(b, a, noise)
            
        return noise

    def _generate_triangle(self, frequency: float, duration: float) -> np.ndarray:
        """Generate triangle wave."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1

    def _apply_effects(self, signal: np.ndarray, effects: Dict[str, Any]) -> np.ndarray:
        """Apply audio effects to signal."""
        processed = signal.copy()
        
        for effect, params in effects.items():
            if effect == "reverb":
                processed = self._apply_reverb(processed, params)
            elif effect == "filter":
                processed = self._apply_filter(processed, params)
                
        return processed

    def _apply_reverb(self, signal: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply simple reverb effect."""
        delay_samples = int(params.get("delay", 0.1) * self.sample_rate)
        decay = params.get("decay", 0.5)
        
        if delay_samples == 0:
            return signal
            
        delayed = np.zeros_like(signal)
        delayed[delay_samples:] = signal[:-delay_samples]
        
        return signal + decay * delayed

    def _apply_filter(self, signal: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply filter effect."""
        from scipy import signal as sig
        
        filter_type = params.get("type", "lowpass")
        cutoff = params.get("cutoff", 1000)
        order = params.get("order", 4)
        
        nyquist = self.sample_rate / 2
        normalized_cutoff = min(cutoff / nyquist, 0.99)
        
        if filter_type == "lowpass":
            b, a = sig.butter(order, normalized_cutoff, btype="low")
        elif filter_type == "highpass":
            b, a = sig.butter(order, normalized_cutoff, btype="high")
        else:
            return signal
            
        return sig.filtfilt(b, a, signal)

class AudioMapper:
    """Map network features to audio parameters."""
    
    def __init__(self):
        self._feature_mappings: Dict[str, Dict[str, Any]] = {
            "packet_size": {
                "param": "frequency",
                "range": (200, 2000),  # Hz
                "profile_mapping": {
                    "ambient": (200, 800),
                    "musical": (440, 880),
                    "nature": (300, 1200),
                    "abstract": (500, 2000),
                    "alert": (300, 3000)
                }
            },
            "protocol_type": {
                "param": "amplitude",
                "range": (0.3, 0.9),
                "profile_mapping": {
                    "ambient": (0.4, 0.7),
                    "musical": (0.5, 0.8),
                    "nature": (0.4, 0.7),
                    "abstract": (0.5, 0.8),
                    "alert": (0.6, 0.9)
                }
            },
            "port_range": {
                "param": "duration",
                "range": (0.1, 0.5),
                "profile_mapping": {
                    "ambient": (0.2, 0.4),
                    "musical": (0.15, 0.3),
                    "nature": (0.3, 0.5),
                    "abstract": (0.1, 0.3),
                    "alert": (0.1, 0.2)
                }
            }
        }
        self._waveform_mapping = {
            "TCP": {
                "ambient": "filtered_noise",
                "musical": "sine",
                "nature": "noise",
                "abstract": "sine",
                "alert": "sawtooth"
            },
            "UDP": {
                "ambient": "sine",
                "musical": "triangle",
                "nature": "filtered_noise",
                "abstract": "square",
                "alert": "square"
            },
            "ICMP": {
                "ambient": "filtered_noise",
                "musical": "sine",
                "nature": "noise",
                "abstract": "sine",
                "alert": "sawtooth"
            },
            "default": {
                "ambient": "filtered_noise",
                "musical": "sine",
                "nature": "noise",
                "abstract": "sine",
                "alert": "square"
            }
        }
        self._current_profile = "ambient"

    def set_profile(self, profile_name: str) -> None:
        """Set current audio profile."""
        if profile_name not in ["ambient", "musical", "nature", "abstract", "alert"]:
            raise ValueError(f"Unknown profile: {profile_name}")
        self._current_profile = profile_name

    def map_packet(self, feature_set: FeatureSet) -> AudioParameters:
        """Map packet features to audio parameters.
        
        Args:
            feature_set: Extracted packet features
            
        Returns:
            AudioParameters for synthesis
        """
        params = {
            "frequency": 440.0,  # Default frequency
            "amplitude": 0.5,    # Default amplitude
            "duration": 0.1,     # Default duration
            "effects": {}        # No effects by default
        }
        
        # Map features to parameters using profile-specific ranges
        for feature_name, feature_value in feature_set.features.items():
            if feature_name in self._feature_mappings:
                mapping = self._feature_mappings[feature_name]
                param_name = mapping["param"]
                
                # Get profile-specific range
                param_min, param_max = mapping["profile_mapping"][self._current_profile]
                
                # Linear mapping of feature to parameter range
                params[param_name] = param_min + feature_value * (param_max - param_min)
        
        # Determine waveform based on protocol and current profile
        protocol = feature_set.metadata.get("original_packet", {}).protocol
        protocol_mapping = self._waveform_mapping.get(protocol, self._waveform_mapping["default"])
        waveform = protocol_mapping[self._current_profile]
        
        return AudioParameters(
            frequency=params["frequency"],
            amplitude=params["amplitude"],
            waveform=waveform,
            duration=params["duration"],
            effects=params["effects"],
            profile=self._current_profile
        )

    def add_mapping(self, feature_name: str, param_name: str, 
                   value_range: Tuple[float, float]) -> None:
        """Add new feature to parameter mapping.
        
        Args:
            feature_name: Name of the feature to map
            param_name: Name of the audio parameter to map to
            value_range: (min, max) range for the parameter
        """
        self._feature_mappings[feature_name] = {
            "param": param_name,
            "range": value_range
        }
