# Python EPB API Client

A Python client for interacting with the EPB (Electric Power Board) API.

## Installation

```bash
pip install python-epb-api
```

## Usage

```python
import asyncio
from aiohttp import ClientSession
from epb_api import EPBApiClient

async def main():
    async with ClientSession() as session:
        client = EPBApiClient("your_username", "your_password", session)
        
        # Authenticate
        await client.authenticate()
        
        # Get account links
        accounts = await client.get_account_links()
        
        # Get usage data
        for account in accounts:
            account_id = account["power_account"]["account_id"]
            gis_id = account["premise"]["gis_id"]
            usage = await client.get_usage_data(account_id, gis_id)
            print(f"Account {account_id}: {usage}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- Async/await support
- Automatic token refresh
- Error handling
- Type hints
- Comprehensive test coverage

## API Methods

### `authenticate()`

Authenticates with the EPB API.

### `get_account_links()`

Gets a list of linked accounts and their details.

### `get_usage_data(account_id: str, gis_id: str | None)`

Gets usage data for a specific account.

## Error Handling

The client provides two custom exception classes:

- `EPBApiError`: Base exception for all API errors
- `EPBAuthError`: Specific to authentication failures

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 