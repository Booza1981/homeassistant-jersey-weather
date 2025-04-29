"""Weather platform for Jersey Weather integration."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List

from homeassistant.components.weather import (
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

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units.
        
        This method is called when a consumer is subscribing to forecast updates.
        """
        if not self.available:
            _LOGGER.debug("No forecast data available")
            return None
        
        forecast_list = []
        
        try:
            today = datetime.now()
            
            for day_index, day in enumerate(self.coordinator.data["forecast"]["forecastDay"]):
                day_name = day.get("dayName", "").strip()
                
                # Parse date from day name and create proper datetime object
                forecast_date = today
                if day_index > 0:
                    try:
                        if day_name in ["Tonight", "Today"]:
                            # Use today for "Tonight" or "Today"
                            forecast_date = today
                        else:
                            # Try to extract date parts for other days (e.g., "Wed 30 Apr")
                            parts = day_name.split()
                            if len(parts) >= 3:
                                # Handle day/month format
                                day_num = int(parts[1])
                                month_name = parts[2]
                                # Convert month name to number
                                months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
                                        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
                                month_num = months.get(month_name, today.month)
                                
                                # Create date object at noon to avoid timezone issues
                                forecast_date = today.replace(
                                    day=day_num, 
                                    month=month_num, 
                                    hour=12, 
                                    minute=0, 
                                    second=0, 
                                    microsecond=0
                                )
                                # If the date is in the past, it might be next year
                                if forecast_date.date() < today.date():
                                    forecast_date = forecast_date.replace(year=today.year + 1)
                    except (ValueError, IndexError) as e:
                        _LOGGER.debug("Could not parse date from day name %s: %s", day_name, e)
                        # Use today plus day_index at noon time if parsing fails
                        forecast_date = (today + timedelta(days=day_index)).replace(
                            hour=12, minute=0, second=0, microsecond=0
                        )

                # Format datetime in RFC 3339 format
                iso_date = forecast_date.isoformat(timespec='seconds') + 'Z'  # UTC time
                
                # Convert temperatures to float
                try:
                    max_temp = float(day.get("maxTemp", "0").replace("°C", ""))
                    min_temp = float(day.get("minTemp", "0").replace("°C", ""))
                except (ValueError, TypeError):
                    max_temp = 0
                    min_temp = 0
                    
                # Get windspeed - try several fields based on order of preference
                wind_speed = 0
                for wind_field in ["windspeedKMAfternoon", "windspeedKMMorning", "windspeedKMEvening"]:
                    try:
                        if day.get(wind_field):
                            wind_speed = float(day.get(wind_field, 0))
                            break
                    except (ValueError, TypeError):
                        pass
                
                # Get wind direction - try several fields
                wind_dir = None
                for dir_field in ["windDirectionAfternoon", "windDirectionMorning", "windDirectionEvening"]:
                    if day.get(dir_field):
                        wind_dir = day.get(dir_field)
                        break
                
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
                
                # Calculate wind bearing from direction
                wind_bearing = None
                if wind_dir:
                    direction_map = {
                        "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5, 
                        "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
                        "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
                        "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5
                    }
                    wind_bearing = direction_map.get(wind_dir)
                
                # Create forecast data dictionary
                forecast_data = {
                    "datetime": iso_date,
                    "condition": condition,
                    "native_temperature": max_temp,
                    "native_templow": min_temp,
                    "native_wind_speed": wind_speed,
                    "precipitation_probability": precip_prob
                }
                
                # Add wind bearing if available
                if wind_bearing is not None:
                    forecast_data["wind_bearing"] = wind_bearing
                
                # Add icon info
                tooltip = day.get("dayToolTip")
                if tooltip:
                    forecast_data["icon_description"] = tooltip
                
                forecast_list.append(forecast_data)
                
            _LOGGER.debug("Generated forecast data with %d days", len(forecast_list))
            return forecast_list
                    
        except (KeyError, ValueError) as e:
            _LOGGER.error("Error parsing forecast data: %s", e)
            return None
