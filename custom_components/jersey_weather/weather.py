"""Weather platform for Jersey Weather integration."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.components.weather import (
    ATTR_FORECAST_CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime

from .const import CONDITION_MAPPINGS, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jersey Weather weather platform based on config_entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.debug("Setting up weather platform with coordinator data: %s", 
                  "available" if coordinator.data else "not available")
    
    async_add_entities([JerseyWeather(coordinator)])


class JerseyWeather(CoordinatorEntity, WeatherEntity):
    """Implementation of Jersey Weather as a weather entity."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator):
        """Initialize Jersey Weather."""
        super().__init__(coordinator)
        self._attr_unique_id = "jersey_weather"
        self._attr_name = "Home"  # Name matches other weather providers
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "jersey_weather")},
            "name": "Jersey Weather",
            "manufacturer": "Jersey Met",
            "model": "Weather API",
            "sw_version": "1.0",
            "configuration_url": "https://www.gov.je/weather/"
        }
        self._attr_attribution = "Weather data provided by Jersey Met"
        _LOGGER.debug("Initialized weather entity with coordinator data: %s", 
                     "available" if coordinator.data else "not available")

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        if not self.coordinator.data:
            return False
        return "forecast" in self.coordinator.data

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        if not self.available:
            return None
            
        try:
            # Get the icon for today
            icon = self.coordinator.data["forecast"]["forecastDay"][0].get("dayIcon")
            
            # Map icon to HA condition
            return CONDITION_MAPPINGS.get(icon, "cloudy")
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting condition: %s", e)
            return None

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.available:
            return None
            
        temp_str = self.coordinator.data["forecast"].get("currentTemprature", "")
        if not temp_str:
            return None
            
        try:
            return float(temp_str.replace("°C", ""))
        except (ValueError, TypeError) as e:
            _LOGGER.error("Error parsing temperature: %s", e)
            return None
            
    @property
    def humidity(self) -> int | None:
        """Return the humidity."""
        # Not provided by the API, but required by some cards
        return None
            
    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        if not self.available:
            return None
            
        try:
            return float(self.coordinator.data["forecast"]["forecastDay"][0].get("windSpeedKM", 0))
        except (KeyError, IndexError, ValueError) as e:
            _LOGGER.error("Error getting wind speed: %s", e)
            return None

    @property
    def wind_bearing(self) -> float | str | None:
        """Return the wind bearing."""
        if not self.available:
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
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting wind bearing: %s", e)
            return None

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return the forecast array."""
        if not self.available:
            _LOGGER.debug("No forecast data available")
            return None
        
        forecast_list = []
        day_names = {"Tonight": "Tonight", "Today": "Today"}
        
        try:
            today = datetime.now().date()
            
            for day_index, day in enumerate(self.coordinator.data["forecast"]["forecastDay"]):
                day_name = day.get("dayName", "").strip()
                
                # Parse date from day name if possible (e.g., "Wed 30 Apr", "Thu 1 May")
                date_obj = today
                if day_index > 0:
                    try:
                        # Try to extract date parts
                        parts = day_name.split()
                        if len(parts) >= 3:
                            # Handle day/month format
                            day_num = int(parts[1])
                            month_name = parts[2]
                            # Convert month name to number
                            months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
                                    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
                            month_num = months.get(month_name, today.month)
                            
                            # Create date object
                            date_obj = today.replace(day=day_num, month=month_num)
                            # If the date is in the past, it might be next year
                            if date_obj < today:
                                date_obj = date_obj.replace(year=today.year + 1)
                    except (ValueError, IndexError) as e:
                        _LOGGER.debug("Could not parse date from day name %s: %s", day_name, e)
                        # Use today plus day_index if parsing fails
                        date_obj = today + timedelta(days=day_index)

                # Format the ISO date for the forecast
                iso_date = date_obj.isoformat()
                
                # Convert temperatures to float
                try:
                    max_temp = float(day.get("maxTemp", "0").replace("°C", ""))
                    min_temp = float(day.get("minTemp", "0").replace("°C", ""))
                except (ValueError, TypeError):
                    max_temp = 0
                    min_temp = 0
                    
                # Convert wind speed to float
                try:
                    wind_speed = float(day.get("windSpeedKM", 0))
                except (ValueError, TypeError):
                    wind_speed = 0
                
                # Get condition from icon
                icon = day.get("dayIcon", "")
                condition = CONDITION_MAPPINGS.get(icon, "cloudy")
                
                # Get precipitation probability (default to highest of morning/afternoon/evening)
                precip_prob = 0
                for period in ["rainProbMorning", "rainProbAfternoon", "rainProbEvening"]:
                    try:
                        prob = int(day.get(period, 0) or 0)
                        precip_prob = max(precip_prob, prob)
                    except (ValueError, TypeError):
                        pass
                
                # Get wind bearing
                wind_dir = day.get("windDirection", "")
                wind_bearing = None
                direction_map = {
                    "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5, 
                    "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
                    "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
                    "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5
                }
                if wind_dir in direction_map:
                    wind_bearing = direction_map[wind_dir]
                
                # Create forecast object
                forecast_data = {
                    ATTR_FORECAST_TIME: iso_date,
                    ATTR_FORECAST_CONDITION: condition,
                    ATTR_FORECAST_NATIVE_TEMP: max_temp,
                    ATTR_FORECAST_NATIVE_TEMP_LOW: min_temp,
                    ATTR_FORECAST_NATIVE_WIND_SPEED: wind_speed,
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY: precip_prob,
                }
                
                # Add wind bearing if available
                if wind_bearing is not None:
                    forecast_data[ATTR_FORECAST_WIND_BEARING] = wind_bearing
                
                forecast_list.append(forecast_data)
                
            _LOGGER.debug("Generated forecast data with %d days", len(forecast_list))
            return forecast_list
                    
        except (KeyError, ValueError) as e:
            _LOGGER.error("Error parsing forecast data: %s", e)
            return None
