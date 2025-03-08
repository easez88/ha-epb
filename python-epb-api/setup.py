from setuptools import setup, find_packages

# Read README.md for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="python-epb-api",
    version="0.1.0",
    description="API client for EPB (Electric Power Board) energy usage data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="asachs",
    author_email="",  # Add your email if you want
    url="https://github.com/asachs01/python-epb-api",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "attrs>=21.0.0",
        "multidict>=4.0.0",
        "yarl>=1.0.0",
        "frozenlist>=1.0.0",
        "typing-extensions>=4.0.0",  # For Python 3.9 compatibility
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="epb energy utility api client homeassistant",
) 