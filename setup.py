from setuptools import find_packages, setup

setup(
    name="ha-epb",
    version="1.0.0",
    description="Home Assistant integration for EPB (Electric Power Board)",
    author="Aaron Sachs",
    author_email="asachs01@users.noreply.github.com",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
    ],
)
