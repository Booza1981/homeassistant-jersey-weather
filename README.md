# Jersey Weather Integration for Home Assistant

<div align="center">
  <img src="images/logo.png" alt="Jersey Met Logo" width="200">
  
  [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
</div>

This custom integration fetches weather data from the Jersey Met service and makes it available in Home Assistant. The integration provides real-time weather conditions, forecasts, tide information, and maritime data for Jersey, Channel Islands.

## Features

- Current weather conditions (temperature, wind, weather state)
- 5-day weather forecast
- UV index information
- Tide information
- Weather images (radar, satellite, wind waves, sea state)
- Maritime data (sea temperature, coastal reports)
- Airport pressure and weather data

## Installation

### HACS Installation (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Navigate to HACS → Integrations → ⋮ (three dots in top right) → Custom repositories
3. Add `https://github.com/Booza1981/homeassistant-jersey-weather` as a custom repository with category "Integration"
4. Click "Download" on the Jersey Weather integration
5. Restart Home Assistant
6. Add the integration from the Integrations page in Home Assistant

### Manual Installation

1. Copy the `custom_components/jersey_weather` directory to your Home Assistant `/config/custom_components` directory.
2. Restart Home Assistant.
3. Go to "Configuration" → "Integrations" and click "+ Add Integration".
4. Search for "Jersey Weather" and follow the setup instructions.

## Configuration

This integration requires no configuration. Simply add it through the Home Assistant UI, and it will automatically fetch data from the Jersey Weather API.

## Entities Created

This integration creates various entities to represent Jersey weather information:

### Sensors
- `sensor.current_temperature`: Current temperature in Jersey
- `sensor.wind_speed`: Current wind speed
- `sensor.wind_direction`: Current wind direction
- `sensor.uv_index`: Current UV index
- `sensor.rain_probability`: Chance of rain with morning/afternoon/evening details
- `sensor.weather_condition`: Current weather condition
- `sensor.sunrise`: Today's sunrise time
- `sensor.sunset`: Today's sunset time
- `sensor.tide_1` through `sensor.tide_4`: Today's tide information (high/low, times, heights)
- `sensor.jersey_airport_pressure`: Current atmospheric pressure at Jersey Airport
- `sensor.sea_temperature`: Current sea temperature around Jersey

### Weather Entity
- `weather.home`: A complete weather entity with current conditions and 5-day forecast

### Cameras
- `camera.radar`: Radar image
- `camera.satellite`: Satellite image
- `camera.jersey_wind_waves`: Wind waves image
- `camera.jersey_sea_state_am`: Sea state AM image
- `camera.jersey_sea_state_pm`: Sea state PM image

## API Information

This integration uses data from the Jersey Met service API endpoints:

- Weather forecast: `https://prodgojweatherstorage.blob.core.windows.net/data/jerseyForecast.json`
- Tide data: `https://prodgojweatherstorage.blob.core.windows.net/data/JerseyTide5Day.json`
- Coastal reports: `https://prodgojweatherstorage.blob.core.windows.net/data/CoastalReports.json`
- Shipping forecast: `https://prodgojweatherstorage.blob.core.windows.net/data/Shipping.json`
- Weather images: Various endpoints under `https://sojpublicdata.blob.core.windows.net/jerseymet/`

## Troubleshooting

If you encounter issues with the integration:

1. Check that your Home Assistant instance has internet access
2. Verify that the Jersey Weather API endpoints are accessible
3. Check the Home Assistant logs for error messages from the `jersey_weather` component
4. Make sure you've restarted Home Assistant after installation

## Example Dashboard

Here's an example of how you might set up a dashboard with all the Jersey Weather data:

```yaml
type: vertical-stack
cards:
  - type: weather-forecast
    entity: weather.home
    show_forecast: true
  - type: horizontal-stack
    cards:
      - type: sensor
        entity: sensor.current_temperature
        name: Temperature
      - type: sensor
        entity: sensor.jersey_airport_pressure
        name: Pressure
      - type: sensor
        entity: sensor.sea_temperature
        name: Sea Temp
  - type: horizontal-stack
    cards:
      - type: sensor
        entity: sensor.wind_speed
        name: Wind Speed
      - type: sensor
        entity: sensor.wind_direction
        name: Direction
      - type: sensor
        entity: sensor.rain_probability
        name: Rain Chance
```

## Credits

- Data source: [Jersey Met](https://www.gov.je/weather/) service (Government of Jersey)
- Logo based on the official Jersey Met branding

## License

This project is licensed under the MIT License - see the LICENSE file for details.
