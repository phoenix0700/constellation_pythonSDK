"""
Setup script for Constellation Python SDK.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="constellation-sdk",
    version="1.2.0",
    author="Constellation Network Community",
    author_email="community@constellationnetwork.io",
    description="Python SDK for Constellation Network (Hypergraph)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/constellation-network/python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "constellation=constellation_sdk.cli:main",
        ],
    },
    keywords="constellation network hypergraph dag blockchain cryptocurrency",
    project_urls={
        "Bug Reports": "https://github.com/constellation-network/python-sdk/issues",
        "Source": "https://github.com/constellation-network/python-sdk",
        "Documentation": "https://docs.constellationnetwork.io/",
    },
) 