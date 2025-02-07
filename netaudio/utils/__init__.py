"""Utility functions and configuration management."""

import os
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """Audio configuration settings."""
    sample_rate: int = 44100
    buffer_size: int = 1024
    channels: int = 1
    format: str = "wav"

@dataclass
class CaptureConfig:
    """Network capture configuration settings."""
    interface: Optional[str] = None
    buffer_size: int = 65535
    timeout: float = 1.0
    promiscuous: bool = False

@dataclass
class ProcessingConfig:
    """Feature processing configuration settings."""
    window_size: float = 1.0
    window_overlap: float = 0.5
    feature_ranges: Dict[str, tuple] = None

    def __post_init__(self):
        if self.feature_ranges is None:
            self.feature_ranges = {
                "packet_size": (0, 65535),
                "protocol_type": (0, 1),
                "port_range": (0, 65535)
            }

class ConfigManager:
    """Manage configuration settings."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self._default_config_path()
        self.audio = AudioConfig()
        self.capture = CaptureConfig()
        self.processing = ProcessingConfig()
        
        # Load config if exists
        if os.path.exists(self.config_path):
            self.load_config()

    def _default_config_path(self) -> str:
        """Get default configuration file path."""
        config_dir = os.path.join(str(Path.home()), ".netaudio")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Update audio config
            if 'audio' in config:
                self.audio = AudioConfig(**config['audio'])
                
            # Update capture config
            if 'capture' in config:
                self.capture = CaptureConfig(**config['capture'])
                
            # Update processing config
            if 'processing' in config:
                self.processing = ProcessingConfig(**config['processing'])
                
            logger.info(f"Loaded configuration from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")

    def save_config(self) -> None:
        """Save current configuration to file."""
        config = {
            'audio': {
                'sample_rate': self.audio.sample_rate,
                'buffer_size': self.audio.buffer_size,
                'channels': self.audio.channels,
                'format': self.audio.format
            },
            'capture': {
                'interface': self.capture.interface,
                'buffer_size': self.capture.buffer_size,
                'timeout': self.capture.timeout,
                'promiscuous': self.capture.promiscuous
            },
            'processing': {
                'window_size': self.processing.window_size,
                'window_overlap': self.processing.window_overlap,
                'feature_ranges': self.processing.feature_ranges
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

class Validator:
    """Validate input data and parameters."""
    
    @staticmethod
    def validate_audio_params(params: Dict[str, Any]) -> bool:
        """Validate audio parameters.
        
        Args:
            params: Audio parameters to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        if 'frequency' in params:
            if not 20 <= params['frequency'] <= 20000:
                raise ValueError("Frequency must be between 20 and 20000 Hz")
                
        if 'amplitude' in params:
            if not 0 <= params['amplitude'] <= 1:
                raise ValueError("Amplitude must be between 0 and 1")
                
        if 'duration' in params:
            if not 0 < params['duration'] <= 10:
                raise ValueError("Duration must be between 0 and 10 seconds")
                
        return True

    @staticmethod
    def validate_packet_data(packet: Dict[str, Any]) -> bool:
        """Validate packet data.
        
        Args:
            packet: Packet data to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        required_fields = ['timestamp', 'size', 'protocol']
        for field in required_fields:
            if field not in packet:
                raise ValueError(f"Missing required field: {field}")
                
        if not isinstance(packet['timestamp'], (int, float)):
            raise ValueError("Timestamp must be numeric")
            
        if not isinstance(packet['size'], int) or packet['size'] < 0:
            raise ValueError("Size must be a positive integer")
            
        if not isinstance(packet['protocol'], str):
            raise ValueError("Protocol must be a string")
            
        return True

    @staticmethod
    def validate_feature_ranges(ranges: Dict[str, tuple]) -> bool:
        """Validate feature ranges.
        
        Args:
            ranges: Feature ranges to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        for feature, (min_val, max_val) in ranges.items():
            if not isinstance(min_val, (int, float)):
                raise ValueError(f"Invalid minimum value for {feature}")
                
            if not isinstance(max_val, (int, float)):
                raise ValueError(f"Invalid maximum value for {feature}")
                
            if min_val >= max_val:
                raise ValueError(f"Invalid range for {feature}: min >= max")
                
        return True
