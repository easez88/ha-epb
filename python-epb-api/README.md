# Python EPB API Client

A Python client for interacting with the EPB (Electric Power Board) API. This client provides functionality to:

- Authenticate with the EPB API
- Fetch account information
- Retrieve power usage data
- Calculate costs based on EPB's rate structure

## Installation

```bash
pip install python-epb-api
```

## Usage

```python
from epb_api import EPBApiClient
from aiohttp import ClientSession

async def main():
    async with ClientSession() as session:
        client = EPBApiClient("your_username", "your_password", session)
        
        # Authenticate
        await client.authenticate()
        
        # Get account links
        accounts = await client.get_account_links()
        
        # Get usage data
        usage = await client.get_usage_data(account_id="your_account_id", gis_id="your_gis_id")
        print(f"Current usage: {usage['kwh']} kWh")
        print(f"Estimated cost: ${usage['cost']:.2f}")

```

## Rate Calculation

The client calculates costs using EPB's current rate structure:
- Base Energy Charge: $0.095 per kWh
- TVA Fuel Cost Adjustment: $0.029 per kWh
- Customer Charge: $9.81 (monthly fixed charge)

## Requirements

- Python 3.9 or higher
- aiohttp>=3.8.0

## License

MIT License 