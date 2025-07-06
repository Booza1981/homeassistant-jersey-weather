"""Weather platform for Jersey Weather integration."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from collections import Counter

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

from .const import CONDITION_MAPPINGS, TOOLTIP_CONDITION_MAPPINGS, SUMMARY_CONDITION_MAPPINGS, DOMAIN

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
        # Set initial attribution
        self._update_attribution()
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
            
            # Check current time to determine day/night conditions
            current_hour = datetime.now().hour
            is_night = current_hour < 6 or current_hour >= 20
            
            # Determine appropriate condition based on time of day and other factors
            if condition is None:
                # Try to infer condition from summary and descriptions
                summary = self.coordinator.data["forecast"]["forecastDay"][0].get("summary", "")
                night_desc = self.coordinator.data["forecast"]["forecastDay"][0].get("nightDescripiton", "")
                morning_desc = self.coordinator.data["forecast"]["forecastDay"][0].get("morningDescripiton", "")
                afternoon_desc = self.coordinator.data["forecast"]["forecastDay"][0].get("afternoonDescripiton", "")
                
                # Look for key terms in all descriptions
                desc_text = (summary + " " + night_desc + " " + morning_desc + " " + afternoon_desc).lower()
                
                # Try to find matches in summary mappings
                for key, value in SUMMARY_CONDITION_MAPPINGS.items():
                    if key in desc_text:
                        if is_night and value == "sunny":
                            condition = "clear-night"
                        else:
                            condition = value
                        _LOGGER.debug("Found condition %s from keyword %s in descriptions", condition, key)
                        break
                
                # If still no condition, use time-appropriate defaults
                if condition is None:
                    if is_night:
                        condition = "clear-night"
                    else:
                        condition = "sunny"
            
            # Make sure night conditions are used at night
            elif is_night and condition == "sunny":
                condition = "clear-night"
            
            _LOGGER.debug("Final condition: %s", condition)
            return condition
            
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting current condition: %s", e)
            return "cloudy"  # Return a safe default
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
        # Not provided by the API
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
    def uv_index(self) -> int | None:
        """Return the UV index."""
        if not self.available:
            return None
        
        try:
            return int(self.coordinator.data["forecast"]["forecastDay"][0].get("uvIndex", 0))
        except (ValueError, TypeError):
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
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if not self.available:
            return {}

        attributes = {}
        forecast_days = self.coordinator.data["forecast"]["forecastDay"]
        today = datetime.now().date()

        # Define condition priority from most to least severe
        CONDITION_PRIORITY_MAP = {
            "lightning-rainy": 10,
            "pouring": 9,
            "snowy-rainy": 8,
            "snowy": 7,
            "hail": 6,
            "rainy": 5,
            "fog": 4,
            "cloudy": 3,
            "partlycloudy": 2,
            "sunny": 1,
            "clear-night": 1,
        }

        for i, day_data in enumerate(forecast_days[:5]):
            day_num = i + 1
            
            # Datetime
            forecast_date = today + timedelta(days=i)
            attributes[f"forecast_day_{day_num}_datetime"] = forecast_date.isoformat()

            # High and Low Temperature
            attributes[f"forecast_day_{day_num}_temp_high"] = float(day_data.get("maxTemp", "0").replace("°C", ""))
            attributes[f"forecast_day_{day_num}_temp_low"] = float(day_data.get("minTemp", "0").replace("°C", ""))

            # Precipitation Probability
            precip_prob = 0
            for period in ["rainProbMorning", "rainProbAfternoon", "rainProbEvening"]:
                try:
                    prob_str = day_data.get(period, "0")
                    if prob_str and isinstance(prob_str, str):
                        prob = int(prob_str)
                        precip_prob = max(precip_prob, prob)
                except (ValueError, TypeError):
                    pass
            attributes[f"forecast_day_{day_num}_precipitation_probability"] = precip_prob
            
            # Precipitation Amount - Not available in API data, so set to a default
            attributes[f"forecast_day_{day_num}_precipitation_amount"] = 0.0

            # Wind Speed
            wind_speeds = []
            for period in ["windspeedKMMorning", "windspeedKMAfternoon", "windspeedKMEvening"]:
                try:
                    speed_str = day_data.get(period)
                    if speed_str:
                        wind_speeds.append(float(speed_str))
                except (ValueError, TypeError):
                    pass
            if wind_speeds:
                attributes[f"forecast_day_{day_num}_wind_speed"] = round(sum(wind_speeds) / len(wind_speeds), 1)
            else:
                attributes[f"forecast_day_{day_num}_wind_speed"] = None

            # Wind Bearing
            directions = [day_data.get(f"windDirection{p}") for p in ["Morning", "Afternoon", "Evening"] if day_data.get(f"windDirection{p}")]
            if directions:
                attributes[f"forecast_day_{day_num}_wind_bearing"] = Counter(directions).most_common(1)[0][0]
            else:
                attributes[f"forecast_day_{day_num}_wind_bearing"] = None

            # Summary
            summary_parts = []
            if day_data.get("morningDescripiton"):
                summary_parts.append(f"Morning: {day_data.get('morningDescripiton')}")
            if day_data.get("afternoonDescripiton"):
                summary_parts.append(f"Afternoon: {day_data.get('afternoonDescripiton')}")
            if day_data.get("nightDescripiton"):
                summary_parts.append(f"Night: {day_data.get('nightDescripiton')}")
            attributes[f"forecast_day_{day_num}_summary"] = ". ".join(summary_parts) + "." if summary_parts else day_data.get("summary")

            # Condition
            conditions = []
            for desc_key in ["morningDescripiton", "afternoonDescripiton", "nightDescripiton", "summary"]:
                desc = day_data.get(desc_key, "").lower()
                for keyword, ha_condition in SUMMARY_CONDITION_MAPPINGS.items():
                    if keyword in desc:
                        conditions.append(ha_condition)
            
            if conditions:
                # Sort by severity and pick the most severe
                conditions.sort(key=lambda c: CONDITION_PRIORITY_MAP.get(c, 0), reverse=True)
                day_condition = conditions[0]
            else:
                # Fallback to icon/tooltip based condition
                icon = day_data.get("dayIcon", "")
                tooltip = day_data.get("dayToolTip", "")
                day_condition = CONDITION_MAPPINGS.get(icon)
                if not day_condition and tooltip:
                    day_condition = TOOLTIP_CONDITION_MAPPINGS.get(tooltip)
                if not day_condition:
                    day_condition = "cloudy"
            
            attributes[f"forecast_day_{day_num}_condition"] = day_condition

            # Detailed period-based forecast attributes
            # Maps the period names from the design to the keys used in the API data
            period_mapping = {
                "morning": {
                    "temp": "morningTemp",
                    "desc": "morningDescripiton", "precip": "rainProbMorning",
                    "wind_km": "windspeedKMMorning", "wind_force": "windSpeedForceMorning",
                    "wind_dir": "windDirectionMorning", "confidence": "confidenceMorning",
                    "icon_tooltip": "iconMorningToolTip", "wind_desc": "morningWindDescripiton"
                },
                "afternoon": {
                    "temp": "maxTemp",
                    "desc": "afternoonDescripiton", "precip": "rainProbAfternoon",
                    "wind_km": "windspeedKMAfternoon", "wind_force": "windSpeedForceAfternoon",
                    "wind_dir": "windDirectionAfternoon", "confidence": "confidenceAfternoon",
                    "icon_tooltip": "iconAfternoonToolTip", "wind_desc": "afternoonWindDescripiton"
                },
                "night": {
                    "temp": "minTemp",
                    "desc": "nightDescripiton", "precip": "rainProbEvening",
                    "wind_km": "windspeedKMEvening", "wind_force": "windSpeedForceEvening",
                    "wind_dir": "windDirectionEvening", "confidence": "confidenceNight",
                    "icon_tooltip": "iconNightToolTip", "wind_desc": "nightWindDescripiton"
                }
            }

            for period_name, api_keys in period_mapping.items():
                # Temperature
                try:
                    temp_key = api_keys.get("temp")
                    temp_str = day_data.get(temp_key) if temp_key else None
                    if temp_str:
                        attributes[f"forecast_day_{day_num}_{period_name}_temperature"] = float(temp_str.replace("°C", ""))
                    else:
                        attributes[f"forecast_day_{day_num}_{period_name}_temperature"] = None
                except (ValueError, TypeError):
                    attributes[f"forecast_day_{day_num}_{period_name}_temperature"] = None

                # Description
                description = day_data.get(api_keys["desc"])
                attributes[f"forecast_day_{day_num}_{period_name}_description"] = description

                # Condition
                # Start with a safe default
                period_condition = "cloudy"
                
                # Try to map from tooltip first, as it's more specific
                tooltip = day_data.get(api_keys["icon_tooltip"])
                if tooltip and tooltip in TOOLTIP_CONDITION_MAPPINGS:
                    period_condition = TOOLTIP_CONDITION_MAPPINGS[tooltip]
                # Fallback to inferring from description text
                elif description:
                    desc_lower = description.lower()
                    # Sort by length of keyword to match more specific terms first (e.g., "lightning" before "light")
                    sorted_mappings = sorted(SUMMARY_CONDITION_MAPPINGS.items(), key=lambda item: len(item[0]), reverse=True)
                    for keyword, ha_condition in sorted_mappings:
                        if keyword in desc_lower:
                            period_condition = ha_condition
                            break
                
                attributes[f"forecast_day_{day_num}_{period_name}_condition"] = period_condition

                # Precipitation Probability
                try:
                    precip_prob_str = day_data.get(api_keys["precip"], "0")
                    attributes[f"forecast_day_{day_num}_{period_name}_precipitation_probability"] = int(precip_prob_str) if precip_prob_str else 0
                except (ValueError, TypeError):
                    attributes[f"forecast_day_{day_num}_{period_name}_precipitation_probability"] = 0

                # Wind Speed
                try:
                    wind_speed_str = day_data.get(api_keys["wind_km"])
                    attributes[f"forecast_day_{day_num}_{period_name}_wind_speed"] = float(wind_speed_str) if wind_speed_str else None
                except (ValueError, TypeError):
                    attributes[f"forecast_day_{day_num}_{period_name}_wind_speed"] = None

                # Wind Speed Force
                attributes[f"forecast_day_{day_num}_{period_name}_wind_speed_force"] = day_data.get(api_keys["wind_force"])

                # Wind Bearing
                attributes[f"forecast_day_{day_num}_{period_name}_wind_bearing"] = day_data.get(api_keys["wind_dir"])

                # Confidence
                attributes[f"forecast_day_{day_num}_{period_name}_confidence"] = day_data.get(api_keys["confidence"])

                # Wind Description
                wind_description = day_data.get(api_keys.get("wind_desc"))
                attributes[f"forecast_day_{day_num}_{period_name}_wind_description"] = wind_description

        return attributes
 
    def _update_attribution(self):
        """Update attribution with current timestamp."""
        timestamp = datetime.now().strftime("%H:%M")
        issue_time = ""
        
        # Try to get the actual issue time from the API data
        if self.coordinator.data and "forecast" in self.coordinator.data:
            issue_time = self.coordinator.data["forecast"].get("issuetime", "")
            if issue_time:
                issue_time = f" - Issued at {issue_time}"
                
        self._attr_attribution = f"Weather data from Jersey Met - Updated at {timestamp}{issue_time}"
        
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update the attribution with new timestamp
        self._update_attribution()
        # Let the parent class handle the rest
        super()._handle_coordinator_update()
    
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
