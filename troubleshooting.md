# Jersey Weather Integration Troubleshooting

This document provides solutions for common issues that may occur with the Jersey Weather integration.

## Common Issues

### Integration Not Appearing in Home Assistant

If the Jersey Weather integration doesn't appear in the Home Assistant integration list:

1. Make sure you've copied the `jersey_weather` directory to your Home Assistant `custom_components` directory.
2. Check that you've restarted Home Assistant after copying the files.
3. Check Home Assistant logs for any errors related to the integration.
4. Verify that the directory structure is correct:
   ```
   custom_components/
   └── jersey_weather/
       ├── __init__.py
       ├── manifest.json
       ├── config_flow.py
       ├── sensor.py
       ├── weather.py
       ├── camera.py
       └── const.py
   ```

### No Data Showing in Entities

If the integration is installed but entities show "Unavailable" or no data:

1. Check your internet connection.
2. Verify that the API endpoints are accessible from your Home Assistant instance.
3. Run the `test_api.py` script to check if the API is working correctly.
4. Check Home Assistant logs for any error messages from the `jersey_weather` component.
5. The API might be temporarily unavailable - try again later.

### Incorrect Weather Data

If the weather data doesn't seem correct:

1. Check the "Last Updated" time to see when the data was last refreshed.
2. Force a refresh by restarting the integration.
3. Verify that the Jersey Met website shows the same data.
4. Time zones might be different - check that your Home Assistant time zone is set correctly.

### Weather Images Not Loading

If the radar or satellite images aren't loading:

1. Check that your Home Assistant instance can access external URLs.
2. Verify that the image URLs are still valid using the `test_api.py` script.
3. Some proxy or network configurations might block image URLs - check your network setup.
4. The images are updated periodically, so they might temporarily be unavailable during updates.

## Checking Logs

To see log messages from the integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.jersey_weather: debug
```

After restarting Home Assistant, check the logs for any error messages related to `jersey_weather`.

## Reinstalling the Integration

If you need to reinstall the integration:

1. Go to Settings → Devices & Services in Home Assistant.
2. Find the Jersey Weather integration and remove it.
3. Restart Home Assistant.
4. Delete the `jersey_weather` directory from your `custom_components` directory.
5. Follow the installation instructions again to reinstall.

## Manual API Testing

If you want to manually test the API endpoints:

1. Use the `test_api.py` script provided with the integration:
   ```
   python3 test_api.py
   ```

2. Or use curl to test the endpoints directly:
   ```
   curl -X GET https://prodgojweatherstorage.blob.core.windows.net/data/jerseyForecast.json
   curl -X GET https://prodgojweatherstorage.blob.core.windows.net/data/JerseyTide5Day.json
   ```

## Contact & Support

If you're still experiencing issues:

1. Check if there are any reported issues in the GitHub repository.
2. Open a new issue with detailed information about your problem.
3. Include logs, error messages, and steps to reproduce the issue.
4. Provide information about your Home Assistant version and environment.

## API Status

The Jersey Weather API is maintained by the Government of Jersey. If the API changes or becomes unavailable, this integration may stop working correctly. In such cases, an update to the integration might be required.
