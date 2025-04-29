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

from .const import CONDITION_MAPPINGS, TOOLTIP_CONDITION_MAPPINGS, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jersey Weather weather platform based on config_entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.debug("Setting up weather platform with coordinator data: %s", 
                  "available" if coordinator.data else "not available")
    
    # Create the weather entity
    weather_entity = JerseyWeather(coordinator)
    
    # Log the supported features
    _LOGGER.debug("Weather entity created with supported features: %s", 
                 weather_entity._attr_supported_features)
                 
    async_add_entities([weather_entity])


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
        # Explicitly set supported features again to ensure it's recognized
        self._attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
        _LOGGER.debug("Initialized Jersey Weather entity with coordinator data: %s", 
                     "available" if coordinator.data else "not available")

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        if not self.coordinator.data:
            _LOGGER.debug("No coordinator data available")
            return False
        
        has_forecast = "forecast" in self.coordinator.data
        
        if not has_forecast:
            _LOGGER.debug("No forecast data in coordinator data")
        else:
            # Check if we have forecast days
            has_days = "forecastDay" in self.coordinator.data.get("forecast", {})
            if not has_days:
                _LOGGER.debug("No forecastDay in forecast data")
                return False
                
            # Check if we have at least one day
            days = self.coordinator.data["forecast"].get("forecastDay", [])
            if not days:
                _LOGGER.debug("No days in forecastDay array")
                return False
                
            _LOGGER.debug("Weather data available with %d forecast days", len(days))
            
        return has_forecast

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        if not self.available:
            return None
            
    # Method 2: Callback implementation - this was working in the previous PR
    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units using the callback method.
        
        This was the method used in the previous PR.
        """
        _LOGGER.debug("_async_forecast_daily callback was called by Home Assistant")
        
        try:
            if not self.available:
                _LOGGER.debug("No forecast data available")
                return None
                
            # Just call our property implementation to avoid duplicating code
            return self.forecast_daily
        except Exception as e:
            _LOGGER.error("Error in _async_forecast_daily: %s", e)
            return None
    
    # Method 3: Async method implementation
    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units using an async method.
        
        This is another approach that might be what Home Assistant expects.
        """
        _LOGGER.debug("async_forecast_daily method was called by Home Assistant")
        
        try:
            if not self.available:
                _LOGGER.debug("No forecast data available")
                return None
                
            # Just call our property implementation to avoid duplicating code
            return self.forecast_daily
        except Exception as e:
            _LOGGER.error("Error in async_forecast_daily: %s", e)
            return None
            
        try:
            # Get the icon and tooltip for today
            icon = self.coordinator.data["forecast"]["forecastDay"][0].get("dayIcon")
            tooltip = self.coordinator.data["forecast"]["forecastDay"][0].get("dayToolTip")
            
            _LOGGER.debug("Getting condition for current weather: icon=%s, tooltip=%s", 
                         icon, tooltip)
            
            # Try to get condition from icon mapping first
            condition = CONDITION_MAPPINGS.get(icon, None)
            
            # If condition is not found or icon is missing, try tooltip mapping
            if condition is None and tooltip:
                condition = TOOLTIP_CONDITION_MAPPINGS.get(tooltip, None)
            
            # Default to cloudy if we still don't have a condition
            if condition is None:
                condition = "cloudy"
                _LOGGER.debug("Using default condition 'cloudy' for current weather")
            
            return condition
            
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting current condition: %s", e)
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

    # Method 1: Property implementation
    @property
    def forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units.
        
        This property is the newer recommended approach in Home Assistant for daily forecasts.
        """
        _LOGGER.debug("forecast_daily property was called by Home Assistant")
        
        try:
        if not self.available:
            _LOGGER.debug("No forecast data available")
            return None
        
        forecast_list = []
        
        try:
            today = datetime.now()
            
            for day_index, day in enumerate(self.coordinator.data["forecast"]["forecastDay"]):
                day_name = day.get("dayName", "").strip()
                
                # Parse date from day name and create proper datetime object
                if day_index == 0 and day_name.lower() == "tonight":
                    # For "Tonight", use today's date with evening time (8 PM)
                    forecast_date = today.replace(hour=20, minute=0, second=0, microsecond=0)
                    _LOGGER.debug("Using evening time for Tonight forecast: %s", forecast_date)
                else:
                    # For other days, try to extract date or use index-based approach
                    forecast_date = None
                    
                    if day_name.lower() in ["today", "tonight"]:
                        # Use today for "Today" or "Tonight"
                        forecast_date = today.replace(hour=12, minute=0, second=0, microsecond=0)
                    else:
                        try:
                            # Try to extract date parts for other days (e.g., "Wed 30 Apr")
                            parts = day_name.split()
                            if len(parts) >= 3:
                                # Handle day/month format
                                try:
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
                                        
                                    _LOGGER.debug("Parsed date from %s: %s", day_name, forecast_date)
                                except (ValueError, IndexError) as e:
                                    _LOGGER.debug("Error parsing day/month from %s: %s", day_name, e)
                                    forecast_date = None
                        except Exception as e:
                            _LOGGER.debug("General error parsing date %s: %s", day_name, e)
                            forecast_date = None
                    
                    # If we couldn't parse a date, use the day index
                    if forecast_date is None:
                        forecast_date = (today + timedelta(days=day_index)).replace(
                            hour=12, minute=0, second=0, microsecond=0
                        )
                        _LOGGER.debug("Using index-based date for %s: %s", day_name, forecast_date)

                # Format datetime in RFC 3339 format
                iso_date = forecast_date.isoformat()
                _LOGGER.debug("Created ISO date for forecast: %s", iso_date)
                
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
                
                # Get condition from icon with tooltip as fallback
                icon = day.get("dayIcon", "")
                tooltip = day.get("dayToolTip", "")
                
                # Try to get condition from icon mapping first
                condition = CONDITION_MAPPINGS.get(icon, None)
                
                # If condition is not found or icon is missing, try tooltip mapping
                if condition is None and tooltip:
                    condition = TOOLTIP_CONDITION_MAPPINGS.get(tooltip, None)
                
                # Default to cloudy if we still don't have a condition
                if condition is None:
                    condition = "cloudy"
                    _LOGGER.debug("Using default condition 'cloudy' for icon=%s, tooltip=%s", 
                                 icon, tooltip)
                else:
                    _LOGGER.debug("Mapped condition: %s from icon=%s, tooltip=%s", 
                                 condition, icon, tooltip)
                
                # Get detailed weather description
                summary = day.get("summary", "")
                
                # Get precipitation probability (default to highest of morning/afternoon/evening)
                precip_prob = 0
                for period in ["rainProbMorning", "rainProbAfternoon", "rainProbEvening"]:
                    try:
                        prob_str = day.get(period, "0")
                        if prob_str and isinstance(prob_str, str):
                            prob = int(prob_str)
                            precip_prob = max(precip_prob, prob)
                    except (ValueError, TypeError) as e:
                        _LOGGER.debug("Error parsing precipitation probability %s: %s", 
                                     day.get(period, ""), e)
                
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
                
                # Create forecast data dictionary with proper formatting
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
                
                # Add additional info for debugging and future use
                day_description = []
                if day.get("summary"):
                    day_description.append(day.get("summary"))
                if day.get("morningDescripiton"):  # Note: API has typo in key name
                    day_description.append(f"Morning: {day.get('morningDescripiton')}")
                if day.get("afternoonDescripiton"):  # Note: API has typo in key name
                    day_description.append(f"Afternoon: {day.get('afternoonDescripiton')}")
                if day.get("nightDescripiton"):  # Note: API has typo in key name
                    day_description.append(f"Night: {day.get('nightDescripiton')}")
                
                if day_description:
                    forecast_data["icon_description"] = " ".join(day_description)
                
                # Add sunrise/sunset times if available
                if day.get("sunRise"):
                    forecast_data["sunrise"] = day.get("sunRise")
                if day.get("sunSet"):
                    forecast_data["sunset"] = day.get("sunSet")
                    
                # Add UV index if available
                if day.get("uvIndex"):
                    try:
                        uv_index = int(day.get("uvIndex", "0"))
                        forecast_data["uv_index"] = uv_index
                    except (ValueError, TypeError):
                        pass
                
                forecast_list.append(forecast_data)
                
            _LOGGER.debug("Generated forecast data with %d days", len(forecast_list))
            
            # Log the first forecast entry for debugging
            if forecast_list:
                _LOGGER.debug("First forecast entry: %s", forecast_list[0])
                
            return forecast_list
                    
        except (KeyError, ValueError) as e:
            _LOGGER.error("Error parsing forecast data: %s", e)
            return None
        except Exception as e:
            _LOGGER.error("Unexpected error in forecast_daily: %s", e, exc_info=True)
            return None
