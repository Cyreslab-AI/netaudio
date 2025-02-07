from setuptools import setup, find_packages

setup(
    name="netaudio",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "scapy>=2.5.0",  # For packet capture and analysis
        "numpy>=1.21.0",  # For numerical operations
        "scipy>=1.7.0",   # For signal processing
        "pyaudio>=0.2.11", # For real-time audio output
        "soundfile>=0.10.0", # For audio file handling
        "python-dotenv>=0.19.0",  # For configuration management
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "mypy>=0.910",
            "isort>=5.9.0",
        ],
    },
    author="Network Audio Team",
    author_email="team@netaudio.org",
    description="A library for transforming network traffic into audio signals",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="network, audio, security, monitoring, anomaly detection",
    url="https://github.com/netaudio/netaudio",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
