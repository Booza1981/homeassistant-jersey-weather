"""Weather platform for Jersey Weather integration."""
import logging
from datetime import datetime, timedelta

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
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
    
    _LOGGER.debug("Setting up weather platform with coordinator data: %s", 
                  "available" if coordinator.data else "not available")
    
    async_add_entities([JerseyWeather(coordinator)])


class JerseyWeather(CoordinatorEntity, WeatherEntity):
    """Implementation of Jersey Weather as a weather entity."""

    _attr_has_entity_name = True
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator):
        """Initialize Jersey Weather."""
        super().__init__(coordinator)
        self._attr_unique_id = "jersey_weather"
        self._attr_name = "Home"  # Changed to match other weather integrations
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "jersey_weather")},
            "name": "Jersey Weather",
            "manufacturer": "Jersey Met",
            "model": "Weather API",
            "sw_version": "1.0",
        }
        _LOGGER.debug("Initialized weather entity with coordinator data: %s", 
                     "available" if coordinator.data else "not available")

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        if not self.coordinator.data:
            return False
        return "forecast" in self.coordinator.data

    @property
    def condition(self):
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
    def native_temperature(self):
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
    def native_wind_speed(self):
        """Return the wind speed."""
        if not self.available:
            return None
            
        try:
            return float(self.coordinator.data["forecast"]["forecastDay"][0].get("windSpeedKM", 0))
        except (KeyError, IndexError, ValueError) as e:
            _LOGGER.error("Error getting wind speed: %s", e)
            return None

    @property
    def wind_bearing(self):
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
    def forecast(self):
        """Return the forecast."""
        if not self.available:
            _LOGGER.debug("No forecast data available")
            return None
            
        forecast_list = []
        
        try:
            # Create forecasts for each day
            for day_index, day in enumerate(self.coordinator.data["forecast"]["forecastDay"]):
                # Parse date from day name (e.g., "Wed 30 Apr", "Thu 1 May")
                day_name = day.get("dayName", "").strip()
                
                # Always include today's forecast
                if day_index == 0:
                    date_str = "Today"
                else:
                    date_str = day_name
                
                # Convert temperatures to float
                try:
                    max_temp = float(day.get("maxTemp", "0").replace("°C", ""))
                    min_temp = float(day.get("minTemp", "0").replace("°C", ""))
                except ValueError:
                    max_temp = 0
                    min_temp = 0
                    
                # Convert wind speed to float
                try:
                    wind_speed = float(day.get("windSpeedKM", 0))
                except ValueError:
                    wind_speed = 0
                
                # Get condition from icon
                icon = day.get("dayIcon", "")
                condition = CONDITION_MAPPINGS.get(icon, "cloudy")
                
                # Get precipitation probability (default to highest of morning/afternoon/evening)
                precip_prob = 0
                for period in ["rainProbMorning", "rainProbAfternoon", "rainProbEvening"]:
                    try:
                        prob = int(day.get(period, 0))
                        precip_prob = max(precip_prob, prob)
                    except (ValueError, TypeError):
                        pass
                
                # Create forecast object
                forecast_data = {
                    "datetime": date_str,
                    "condition": condition,
                    "temperature": max_temp,
                    "templow": min_temp,
                    "wind_speed": wind_speed,
                    "precipitation_probability": precip_prob
                }
                
                forecast_list.append(forecast_data)
                
                # Include up to 5 days
                if len(forecast_list) >= 5:
                    break
                    
            _LOGGER.debug("Generated forecast data with %d days", len(forecast_list))
            return forecast_list
                    
        except (KeyError, ValueError) as e:
            _LOGGER.error("Error parsing forecast data: %s", e)
            return None
