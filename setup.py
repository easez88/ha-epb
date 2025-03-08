"""Setup for EPB integration."""
from setuptools import find_namespace_packages, setup

setup(
    name="ha-epb",
    version="0.0.1",
    description="Home Assistant integration for EPB (Electric Power Board)",
    author="Aaron Sachs",
    author_email="aaronm.sachs@gmail.com",
    packages=find_namespace_packages(include=["custom_components.*"]),
    package_data={
        "custom_components.epb": ["manifest.json", "translations/*.json"]
    },
    install_requires=[
        "aiohttp>=3.8.0",
    ],
    tests_require=[
        "pytest>=7.0.0",
        "pytest-asyncio>=0.20.0",
        "pytest-cov>=4.0.0",
        "homeassistant>=2024.1.0",
    ],
    python_requires=">=3.11.0",
)
