# Home Assistant EPB Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

This is a custom component for Home Assistant that integrates with EPB (Electric Power Board) to provide energy usage and cost data.

## Features

- Real-time energy usage data from EPB
- Daily cost tracking
- Multiple account support
- Automatic data updates every 15 minutes

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/yourusername/ha-epb`
6. Select category: "Integration"
7. Click "Add"
8. Click "Install" on the EPB integration card

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/epb` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "EPB"
4. Enter your EPB credentials:
   - Username (your EPB web portal username)
   - Password (your EPB web portal password)

## Sensors

For each EPB account, this integration creates:

- **EPB Energy**: Daily energy usage in kWh
  - Device class: `energy`
  - State class: `total_increasing`
  - Unit: kWh

- **EPB Cost**: Daily energy cost
  - Device class: `monetary`
  - State class: `total`
  - Unit: USD

## API Details

This integration uses the EPB web API to fetch data:
- Authentication endpoint: `https://api.epb.com/web/api/v1/login/`
- Account data endpoint: `https://api.epb.com/web/api/v1/account-links/`
- Usage data endpoint: `https://api.epb.com/web/api/v1/usage/power/permanent/compare/daily`

Data is updated every 15 minutes by default.

## Debugging

This integration logs to Home Assistant's standard logging system. To see the logs:

1. Go to Settings > System > Logs
2. Filter for "epb"

To enable debug logging, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.epb: debug
```

## Contributing

Feel free to submit issues and pull requests for improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This integration is not officially affiliated with or endorsed by EPB.