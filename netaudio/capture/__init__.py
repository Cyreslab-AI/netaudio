"""Network traffic capture module."""

from abc import ABC, abstractmethod
from typing import Iterator, Optional, Any, Dict, Deque
from dataclasses import dataclass
from contextlib import contextmanager
from collections import deque
import threading

@dataclass
class PacketData:
    """Standardized packet data structure."""
    timestamp: float
    size: int
    protocol: str
    src_port: Optional[int]
    dst_port: Optional[int]
    flags: Dict[str, Any]
    payload: bytes

class CaptureSource(ABC):
    """Abstract base class for network traffic capture sources."""
    
    def __init__(self, buffer_size: int = 1024):
        self.buffer_size = buffer_size
        self._is_running = False

    @abstractmethod
    def start(self) -> None:
        """Start capturing network traffic."""
        self._is_running = True

    @abstractmethod
    def stop(self) -> None:
        """Stop capturing network traffic."""
        self._is_running = False

    @abstractmethod
    def get_packet(self) -> Optional[PacketData]:
        """Get next packet from the capture source."""
        pass

    @contextmanager
    def stream(self) -> Iterator[Iterator[PacketData]]:
        """Stream packets from the capture source."""
        try:
            self.start()
            def packet_generator():
                while self._is_running:
                    packet = self.get_packet()
                    if packet:
                        yield packet
            yield packet_generator()
        finally:
            self.stop()

class LiveCapture(CaptureSource):
    """Live network interface capture implementation."""
    
    def __init__(self, interface: str, buffer_size: int = 1024):
        super().__init__(buffer_size)
        self.interface = interface
        self._capture_handle = None
        self._packet_buffer: Deque[PacketData] = deque(maxlen=buffer_size)
        self._buffer_lock = threading.Lock()

    def start(self) -> None:
        """Start capturing from network interface."""
        try:
            from scapy.all import sniff
            import os
            
            # Ensure we have root privileges for capture
            if os.geteuid() != 0:
                raise PermissionError("Root privileges required for network capture")
                
            # Initialize capture before potentially dropping privileges
            super().start()
            self._capture_handle = sniff(iface=self.interface, store=False, 
                                       prn=self._packet_callback, count=0,
                                       filter="ip")  # Only capture IP packets
        except ImportError:
            raise ImportError("Scapy is required for live capture. Install with: pip install scapy")

    def stop(self) -> None:
        """Stop the live capture."""
        if self._capture_handle:
            self._capture_handle.stop()
        super().stop()

    def get_packet(self) -> Optional[PacketData]:
        """Get next packet from the live capture."""
        with self._buffer_lock:
            return self._packet_buffer.popleft() if self._packet_buffer else None

    def _packet_callback(self, packet: Any) -> None:
        """Process captured packet."""
        from scapy.layers.inet import IP, TCP, UDP, ICMP
        
        if IP in packet:
            # Extract basic packet info
            ip_packet = packet[IP]
            size = len(packet)
            timestamp = float(packet.time)
            
            # Determine protocol and ports
            protocol = "UNKNOWN"
            src_port = None
            dst_port = None
            flags = {}
            
            if TCP in packet:
                protocol = "TCP"
                tcp = packet[TCP]
                src_port = tcp.sport
                dst_port = tcp.dport
                # Extract TCP flags
                flags = {
                    "SYN": (tcp.flags & 0x02) != 0,
                    "ACK": (tcp.flags & 0x10) != 0,
                    "FIN": (tcp.flags & 0x01) != 0,
                    "RST": (tcp.flags & 0x04) != 0,
                    "PSH": (tcp.flags & 0x08) != 0,
                    "URG": (tcp.flags & 0x20) != 0
                }
            elif UDP in packet:
                protocol = "UDP"
                udp = packet[UDP]
                src_port = udp.sport
                dst_port = udp.dport
            elif ICMP in packet:
                protocol = "ICMP"
                icmp = packet[ICMP]
                flags = {
                    "type": icmp.type,
                    "code": icmp.code
                }
            
            # Create standardized packet data
            packet_data = PacketData(
                timestamp=timestamp,
                size=size,
                protocol=protocol,
                src_port=src_port,
                dst_port=dst_port,
                flags=flags,
                payload=bytes(packet.payload)
            )
            
            # Store packet in buffer
            with self._buffer_lock:
                self._packet_buffer.append(packet_data)

class PcapReader(CaptureSource):
    """PCAP file reader implementation."""
    
    def __init__(self, filepath: str, buffer_size: int = 1024):
        super().__init__(buffer_size)
        self.filepath = filepath
        self._reader = None

    def start(self) -> None:
        """Start reading from PCAP file."""
        try:
            from scapy.all import rdpcap
            super().start()
            self._reader = rdpcap(self.filepath)
        except ImportError:
            raise ImportError("Scapy is required for PCAP reading. Install with: pip install scapy")

    def stop(self) -> None:
        """Stop reading from PCAP file."""
        self._reader = None
        super().stop()

    def get_packet(self) -> Optional[PacketData]:
        """Get next packet from the PCAP file."""
        # Implementation for reading from PCAP
        pass
