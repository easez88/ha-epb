# Python EPB API Client

An async Python client for interacting with the EPB (Electric Power Board) API. This client provides functionality to fetch energy usage and cost data from EPB accounts.

## Features

- Async/await support using aiohttp
- Automatic token management and refresh
- Energy usage data retrieval
- Cost calculation using EPB's rate structure
- Type hints for better IDE support
- Comprehensive error handling

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

        # Get usage data for each account
        for account in accounts:
            account_id = account["power_account"]["account_id"]
            gis_id = account["premise"]["gis_id"]
            usage = await client.get_usage_data(account_id, gis_id)
            print(f"Account {account_id}:")
            print(f"  Energy Usage: {usage['kwh']} kWh")
            print(f"  Cost: ${usage['cost']:.2f}")
```

## Rate Calculation

The client calculates costs using EPB's current rate structure:
- Base Energy Charge: $0.095 per kWh
- TVA Fuel Cost Adjustment: $0.029 per kWh
- Customer Charge: $9.81 (monthly fixed charge)

## Error Handling

The client provides two main exception classes:
- `EPBApiError`: Base exception for all API errors
- `EPBAuthError`: Specific to authentication failures

## Requirements

- Python 3.9 or higher
- aiohttp>=3.8.0

## License

MIT License
