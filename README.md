# EPB Integration for Home Assistant

This integration allows you to monitor your Electric Power Board (EPB) energy usage and cost data in Home Assistant.

## Features

- Real-time energy usage monitoring
- Cost tracking
- Multiple account support
- Configurable update intervals
- Automatic token refresh

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the "+" button
4. Search for "EPB"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/epb` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings -> Devices & Services
2. Click "Add Integration"
3. Search for "EPB"
4. Enter your EPB credentials:
   - Username (email)
   - Password
   - Update interval (optional, defaults to 15 minutes)

## Entities

For each EPB account, the integration creates:

- Energy sensor (kWh)
  - Shows current energy usage
  - Includes service address and account details as attributes
- Cost sensor ($)
  - Shows current cost
  - Updates with real-time rate information

## Options

You can configure the following options:
- Update interval (1-60 minutes)

To change options:
1. Go to Settings -> Devices & Services
2. Find the EPB integration
3. Click "Configure"

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify your EPB credentials
   - Check if you can log in to the EPB website

2. **No Data Available**
   - The integration will show as unavailable if no data is received
   - Check your EPB account status

3. **Token Expired**
   - The integration automatically handles token refresh
   - If persistent, try removing and re-adding the integration

### Debug Logging

To enable debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.epb: debug
```

## Contributing

We welcome contributions! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
