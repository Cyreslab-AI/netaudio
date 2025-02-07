"""Network traffic processing and feature extraction module."""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
from ..capture import PacketData

@dataclass
class FeatureSet:
    """Container for extracted features."""
    features: Dict[str, float]
    timestamp: float
    metadata: Dict[str, Any]

class FeatureExtractor:
    """Extract features from network packets."""
    
    def __init__(self):
        self._features: Dict[str, Callable[[PacketData], float]] = {}
        self._initialize_default_features()

    def _initialize_default_features(self) -> None:
        """Initialize default feature extractors."""
        self.add_feature("packet_size", lambda p: float(p.size))
        self.add_feature("protocol_type", lambda p: hash(p.protocol) % 1000 / 1000.0)
        self.add_feature("port_range", lambda p: (p.src_port or 0) / 65535.0)
        
    def add_feature(self, name: str, extractor: Callable[[PacketData], float]) -> None:
        """Add a new feature extractor.
        
        Args:
            name: Feature name
            extractor: Function that extracts the feature from a packet
        """
        self._features[name] = extractor

    def extract(self, packet: PacketData) -> FeatureSet:
        """Extract all registered features from a packet.
        
        Args:
            packet: Packet to extract features from
            
        Returns:
            FeatureSet containing all extracted features
        """
        features = {
            name: extractor(packet)
            for name, extractor in self._features.items()
        }
        return FeatureSet(
            features=features,
            timestamp=packet.timestamp,
            metadata={"original_packet": packet}
        )

class WindowProcessor:
    """Process packets in time windows."""
    
    def __init__(self, window_size: float = 1.0, overlap: float = 0.5):
        """Initialize window processor.
        
        Args:
            window_size: Size of the window in seconds
            overlap: Overlap between windows (0.0 to 1.0)
        """
        self.window_size = window_size
        self.overlap = overlap
        self._buffer: List[FeatureSet] = []
        self._step_size = window_size * (1 - overlap)

    def process(self, feature_set: FeatureSet) -> Optional[np.ndarray]:
        """Process a new feature set.
        
        Args:
            feature_set: New features to process
            
        Returns:
            Processed window data if a window is complete, None otherwise
        """
        self._buffer.append(feature_set)
        
        # Remove old features
        cutoff_time = feature_set.timestamp - self.window_size
        self._buffer = [f for f in self._buffer if f.timestamp > cutoff_time]
        
        # Check if we have enough data for a window
        if len(self._buffer) > 0:
            window_start = self._buffer[-1].timestamp - self.window_size
            window_features = [f for f in self._buffer if f.timestamp > window_start]
            
            if len(window_features) > 0:
                return self._process_window(window_features)
        
        return None

    def _process_window(self, window_features: List[FeatureSet]) -> np.ndarray:
        """Process a complete window of features.
        
        Args:
            window_features: List of feature sets in the window
            
        Returns:
            Processed window data as numpy array
        """
        # Extract all feature names
        feature_names = window_features[0].features.keys()
        
        # Create feature arrays
        feature_arrays = {
            name: np.array([f.features[name] for f in window_features])
            for name in feature_names
        }
        
        # Compute statistics for each feature
        window_stats = []
        for name, values in feature_arrays.items():
            window_stats.extend([
                np.mean(values),
                np.std(values),
                np.max(values),
                np.min(values)
            ])
            
        return np.array(window_stats)

class DataNormalizer:
    """Normalize feature values to a specified range."""
    
    def __init__(self, feature_ranges: Dict[str, Tuple[float, float]]):
        """Initialize normalizer.
        
        Args:
            feature_ranges: Dictionary mapping feature names to (min, max) ranges
        """
        self.feature_ranges = feature_ranges
        self._stats: Dict[str, Dict[str, float]] = {}

    def update_stats(self, feature_set: FeatureSet) -> None:
        """Update running statistics for features.
        
        Args:
            feature_set: New features to update statistics with
        """
        for name, value in feature_set.features.items():
            if name not in self._stats:
                self._stats[name] = {"min": value, "max": value}
            else:
                self._stats[name]["min"] = min(self._stats[name]["min"], value)
                self._stats[name]["max"] = max(self._stats[name]["max"], value)

    def normalize(self, feature_set: FeatureSet) -> FeatureSet:
        """Normalize feature values to their specified ranges.
        
        Args:
            feature_set: Features to normalize
            
        Returns:
            New FeatureSet with normalized values
        """
        normalized_features = {}
        
        for name, value in feature_set.features.items():
            if name in self.feature_ranges:
                target_min, target_max = self.feature_ranges[name]
                stats = self._stats.get(name, {"min": value, "max": value})
                
                # Normalize to [0, 1] then scale to target range
                normalized = (value - stats["min"]) / (stats["max"] - stats["min"])
                normalized = normalized * (target_max - target_min) + target_min
                
                normalized_features[name] = normalized
            else:
                normalized_features[name] = value
                
        return FeatureSet(
            features=normalized_features,
            timestamp=feature_set.timestamp,
            metadata=feature_set.metadata
        )
