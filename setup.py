#!/usr/bin/env python3
"""
NetAudio - Network Traffic Sonification

A Python library for converting network traffic into audio in real-time.
"""

from setuptools import setup, find_packages

setup(
    name="netaudio",
    version="0.1.0",
    description="Network Traffic Sonification",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="NetAudio Team",
    author_email="info@example.com",
    url="https://github.com/example/netaudio",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.19.0",
        "scipy>=1.5.0",
        "sounddevice>=0.4.0",
        "scapy>=2.4.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: System :: Networking :: Monitoring",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "netaudio-demo=examples.enhanced_demo:main",
            "netaudio-traffic=examples.test_traffic_generator:main",
            "netaudio-pcap=examples.pcap_player:main",
            "netaudio-capture=examples.capture_to_pcap:main",
            "netaudio-run=examples.run_demo:main",
        ],
    },
)
