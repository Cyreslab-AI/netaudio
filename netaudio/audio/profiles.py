"""Audio profile definitions and management."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import signal

@dataclass
class AudioProfile:
    """Audio profile configuration."""
    name: str
    frequency_range: Tuple[float, float]
    waveforms: List[str]
    effects: Dict[str, Dict[str, Any]]
    scaling: Dict[str, float]
    musical_scale: Optional[List[float]] = None

class AudioProfileManager:
    """Manage and apply audio profiles."""
    
    def __init__(self):
        self._profiles = {}
        self._current_profile = None
        self._initialize_default_profiles()

    def _initialize_default_profiles(self):
        """Initialize default audio profiles."""
        # Ambient profile - gentle, atmospheric sounds
        self._profiles['ambient'] = AudioProfile(
            name="Ambient",
            frequency_range=(50, 1000),
            waveforms=['filtered_noise', 'sine'],
            effects={
                'reverb': {'mix': 0.3, 'decay': 2.0},
                'lowpass': {'cutoff': 800, 'order': 4}
            },
            scaling={
                'amplitude': 0.6,
                'duration': 1.5
            }
        )

        # Musical profile - harmonious, scale-based sounds
        self._profiles['musical'] = AudioProfile(
            name="Musical",
            frequency_range=(220, 880),  # A3 to A5
            waveforms=['sine', 'triangle'],
            effects={
                'reverb': {'mix': 0.2, 'decay': 1.0},
                'compression': {'threshold': -20, 'ratio': 4.0}
            },
            scaling={
                'amplitude': 0.7,
                'duration': 1.0
            },
            musical_scale=self._generate_pentatonic_scale(220, 880)
        )

        # Nature profile - natural sound approximations
        self._profiles['nature'] = AudioProfile(
            name="Nature",
            frequency_range=(100, 2000),
            waveforms=['noise', 'sine'],
            effects={
                'bandpass': {'center_freq': 500, 'q': 1.0},
                'reverb': {'mix': 0.4, 'decay': 1.5}
            },
            scaling={
                'amplitude': 0.5,
                'duration': 2.0
            }
        )

        # Abstract profile - clean, minimal sounds
        self._profiles['abstract'] = AudioProfile(
            name="Abstract",
            frequency_range=(200, 4000),
            waveforms=['sine', 'square'],
            effects={
                'highpass': {'cutoff': 200, 'order': 2},
                'compression': {'threshold': -15, 'ratio': 3.0}
            },
            scaling={
                'amplitude': 0.4,
                'duration': 0.5
            }
        )

        # Alert profile - technical, detailed sounds
        self._profiles['alert'] = AudioProfile(
            name="Alert",
            frequency_range=(100, 5000),
            waveforms=['sawtooth', 'square', 'sine'],
            effects={
                'compression': {'threshold': -10, 'ratio': 2.0}
            },
            scaling={
                'amplitude': 0.8,
                'duration': 0.3
            }
        )

        # Set default profile
        self._current_profile = self._profiles['ambient']

    def _generate_pentatonic_scale(self, min_freq: float, max_freq: float) -> List[float]:
        """Generate pentatonic scale frequencies within range."""
        # Pentatonic scale intervals (in semitones): 0, 2, 4, 7, 9
        pentatonic_intervals = [0, 2, 4, 7, 9]
        
        # Generate all possible frequencies
        frequencies = []
        current_freq = min_freq
        while current_freq <= max_freq:
            for interval in pentatonic_intervals:
                freq = current_freq * (2 ** (interval / 12))
                if freq <= max_freq:
                    frequencies.append(freq)
            current_freq *= 2  # Move up an octave
            
        return sorted(frequencies)

    def get_profile(self, name: str) -> AudioProfile:
        """Get audio profile by name."""
        return self._profiles.get(name, self._current_profile)

    def set_current_profile(self, name: str) -> None:
        """Set current audio profile."""
        if name in self._profiles:
            self._current_profile = self._profiles[name]
        else:
            raise ValueError(f"Unknown profile: {name}")

    def get_current_profile(self) -> AudioProfile:
        """Get current audio profile."""
        return self._current_profile

    def add_profile(self, name: str, profile: AudioProfile) -> None:
        """Add new audio profile."""
        self._profiles[name] = profile

    def apply_profile(self, signal: np.ndarray, profile: Optional[AudioProfile] = None) -> np.ndarray:
        """Apply profile effects to audio signal."""
        if profile is None:
            profile = self._current_profile

        processed = signal.copy()
        
        # Apply effects
        for effect_name, params in profile.effects.items():
            if effect_name == 'reverb':
                processed = self._apply_reverb(processed, params)
            elif effect_name == 'compression':
                processed = self._apply_compression(processed, params)
            elif effect_name in ['lowpass', 'highpass', 'bandpass']:
                processed = self._apply_filter(processed, effect_name, params)

        # Apply scaling
        processed *= profile.scaling.get('amplitude', 1.0)
        
        return processed

    def _apply_reverb(self, signal: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply reverb effect."""
        mix = params.get('mix', 0.3)
        decay = params.get('decay', 1.0)
        
        # Create simple delay-based reverb
        delay_samples = int(0.05 * 44100)  # 50ms delay
        decay_factor = np.exp(-np.arange(len(signal)) / (decay * 44100))
        
        reverb = np.zeros_like(signal)
        reverb[delay_samples:] = signal[:-delay_samples] * decay_factor[:-delay_samples]
        
        return (1 - mix) * signal + mix * reverb

    def _apply_compression(self, signal: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply dynamic range compression."""
        threshold = params.get('threshold', -20)
        ratio = params.get('ratio', 4.0)
        
        # Convert threshold from dB
        threshold_amp = 10 ** (threshold / 20)
        
        # Compute amplitude envelope
        envelope = np.abs(signal)
        
        # Apply compression
        compressed = np.where(
            envelope > threshold_amp,
            threshold_amp + (envelope - threshold_amp) / ratio,
            envelope
        )
        
        return np.sign(signal) * compressed

    def _apply_filter(self, signal: np.ndarray, filter_type: str, params: Dict[str, Any]) -> np.ndarray:
        """Apply various types of filters."""
        sample_rate = 44100  # Standard sample rate
        nyquist = sample_rate / 2
        
        if filter_type == 'lowpass':
            cutoff = params.get('cutoff', 1000)
            order = params.get('order', 4)
            b, a = signal.butter(order, cutoff / nyquist, btype='low')
            
        elif filter_type == 'highpass':
            cutoff = params.get('cutoff', 1000)
            order = params.get('order', 4)
            b, a = signal.butter(order, cutoff / nyquist, btype='high')
            
        elif filter_type == 'bandpass':
            center_freq = params.get('center_freq', 1000)
            q = params.get('q', 1.0)
            b, a = signal.iirpeak(center_freq / nyquist, q)
            
        return signal.filtfilt(b, a, signal)

    def quantize_to_scale(self, frequency: float, profile: Optional[AudioProfile] = None) -> float:
        """Quantize frequency to nearest note in scale."""
        if profile is None:
            profile = self._current_profile
            
        if profile.musical_scale:
            return min(profile.musical_scale, key=lambda x: abs(x - frequency))
        return frequency
