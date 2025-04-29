# Jersey Weather Integration for Home Assistant

This custom integration fetches weather data from the Jersey Met service and makes it available in Home Assistant.

## Features

- Current weather conditions (temperature, wind, weather state)
- 5-day weather forecast
- UV index information
- Tide information
- Weather images (radar, satellite, wind waves, sea state)

## Installation

### Manual Installation

1. Copy the `custom_components/jersey_weather` directory to your Home Assistant `/config/custom_components` directory.
2. Restart Home Assistant.
3. Go to "Configuration" -> "Integrations" and click "+ Add Integration".
4. Search for "Jersey Weather" and follow the setup instructions.

### HACS Installation

1. Open HACS in your Home Assistant instance.
2. Click on "Integrations".
3. Click the three dots in the top right corner and choose "Custom repositories".
4. Add the URL of this repository and select "Integration" as the category.
5. Click "Add".
6. Search for "Jersey Weather" in the Integrations tab.
7. Click "Install" and restart Home Assistant.

## Usage

Once installed, the integration will create the following entities:

### Sensors
- Current temperature
- Wind direction
- Wind speed
- UV index
- Weather condition
- Sunrise/sunset times
- Tide information (high/low, times, heights)

### Weather Entity
A complete weather entity with current conditions and 5-day forecast.

### Cameras
- Radar image
- Satellite image
- Wind waves
- Sea state (AM and PM)

## Development

This integration uses data from the Jersey Met service API endpoints:

- Weather forecast: `https://prodgojweatherstorage.blob.core.windows.net/data/jerseyForecast.json`
- Tide data: `https://prodgojweatherstorage.blob.core.windows.net/data/JerseyTide5Day.json`
- Weather images: Various endpoints under `https://sojpublicdata.blob.core.windows.net/jerseymet/`

## Credits

- Data source: Jersey Met service (Government of Jersey)
- Integration developed by [Your Name]

## License

This project is licensed under the MIT License - see the LICENSE file for details.
