"""Weather platform for Jersey Weather integration."""
import logging
from datetime import datetime, timedelta

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    TEMP_CELSIUS,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONDITION_MAPPINGS, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jersey Weather weather platform based on config_entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([JerseyWeather(coordinator)])


class JerseyWeather(CoordinatorEntity, WeatherEntity):
    """Implementation of Jersey Weather as a weather entity."""

    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator):
        """Initialize Jersey Weather."""
        super().__init__(coordinator)
        self._attr_unique_id = "jersey_weather"
        self._attr_name = "Jersey Weather"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "jersey_weather")},
            "name": "Jersey Weather",
            "manufacturer": "Jersey Met",
            "model": "Weather API",
            "sw_version": "1.0",
        }

    @property
    def condition(self):
        """Return the current weather condition."""
        if not self.coordinator.data or "forecast" not in self.coordinator.data:
            return None
            
        try:
            # Get the icon for today
            icon = self.coordinator.data["forecast"]["forecastDay"][0].get("dayIcon")
            
            # Map icon to HA condition
            return CONDITION_MAPPINGS.get(icon, "cloudy")
        except (KeyError, IndexError):
            return None

    @property
    def native_temperature(self):
        """Return the current temperature."""
        if not self.coordinator.data or "forecast" not in self.coordinator.data:
            return None
            
        temp_str = self.coordinator.data["forecast"].get("currentTemprature", "")
        if not temp_str:
            return None
            
        try:
            return float(temp_str.replace("°C", ""))
        except (ValueError, TypeError):
            return None

    @property
    def native_wind_speed(self):
        """Return the wind speed."""
        if not self.coordinator.data or "forecast" not in self.coordinator.data:
            return None
            
        try:
            return float(self.coordinator.data["forecast"]["forecastDay"][0].get("windSpeedKM", 0))
        except (KeyError, IndexError, ValueError):
            return None

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        if not self.coordinator.data or "forecast" not in self.coordinator.data:
            return None
            
        try:
            # Convert direction abbreviation to degrees (approximate)
            direction = self.coordinator.data["forecast"]["forecastDay"][0].get("windDirection")
            
            direction_map = {
                "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5, 
                "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
                "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
                "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5
            }
            
            return direction_map.get(direction)
        except (KeyError, IndexError):
            return None

    @property
    def native_pressure(self):
        """Return the pressure."""
        # Not provided in the API
        return None

    @property
    def native_visibility(self):
        """Return the visibility."""
        # Not provided in the API
        return None

    @property
    def native_humidity(self):
        """Return the humidity."""
        # Not provided in the API
        return None

    @property
    def native_apparent_temperature(self):
        """Return the apparent temperature."""
        # Not provided in the API
        return None

    @property
    def native_forecast(self):
        """Return the forecast."""
        if not self.coordinator.data or "forecast" not in self.coordinator.data:
            return None
            
        forecast_list = []
        
        try:
            for day_index, day in enumerate(self.coordinator.data["forecast"]["forecastDay"]):
                # Skip today (index 0) since it's current conditions
                if day_index == 0:
                    continue
                    
                # Parse date
                date_str = day.get("dayName", "")
                
                # Create forecast object
                forecast_data = {
                    "datetime": date_str,
                    "condition": CONDITION_MAPPINGS.get(day.get("dayIcon"), "cloudy"),
                    "native_temperature": float(day.get("maxTemp", "0").replace("°C", "")),
                    "native_templow": float(day.get("minTemp", "0").replace("°C", "")),
                    "native_wind_speed": float(day.get("windSpeedKM", 0)),
                }
                
                # Add precipitation probability if available
                if day.get("rainProbAfternoon"):
                    forecast_data["precipitation_probability"] = int(day.get("rainProbAfternoon", 0))
                
                forecast_list.append(forecast_data)
                
                # Only include 5 days total
                if len(forecast_list) >= 5:
                    break
                    
        except (KeyError, ValueError) as e:
            _LOGGER.error(f"Error parsing forecast data: {e}")
            
        return forecast_list
