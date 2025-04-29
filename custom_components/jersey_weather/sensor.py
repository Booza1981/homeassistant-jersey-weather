"""Sensor platform for Jersey Weather integration."""
import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTime,
)

from .const import (
    ATTR_FORECAST_DATE, 
    ATTR_ISSUE_TIME, 
    ATTR_RAIN_PROBABILITY, 
    ATTR_UV_INDEX,
    ATTR_WIND_DIRECTION, 
    ATTR_WIND_SPEED, 
    ATTR_WIND_SPEED_KM, 
    ATTR_WIND_SPEED_KNOTS, 
    ATTR_WIND_SPEED_MPH,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jersey Weather sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = []
    
    # Current Weather Sensors
    sensors.append(JerseyCurrentTemperatureSensor(coordinator))
    sensors.append(JerseyWindDirectionSensor(coordinator))
    sensors.append(JerseyWindSpeedSensor(coordinator))
    sensors.append(JerseyUVIndexSensor(coordinator))
    sensors.append(JerseyWeatherConditionSensor(coordinator))
    sensors.append(JerseySunriseSensor(coordinator))
    sensors.append(JerseySunsetSensor(coordinator))
    
    # Tide Sensors - we'll create sensors for today's tides
    for i in range(4):  # Usually 4 tide events per day
        sensors.append(JerseyTideSensor(coordinator, i))
    
    async_add_entities(sensors)


class JerseyWeatherSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Jersey Weather sensors."""

    def __init__(self, coordinator, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_has_entity_name = True
        self._attr_unique_id = f"jersey_weather_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "jersey_weather")},
            "name": "Jersey Weather",
            "manufacturer": "Jersey Met",
            "model": "Weather API",
            "sw_version": "1.0",
        }
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("forecast") is not None


class JerseyCurrentTemperatureSensor(JerseyWeatherSensorBase):
    """Sensor for current temperature."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "current_temperature")
        self._attr_name = "Current Temperature"
        self._attr_native_unit_of_measurement = TEMP_CELSIUS
        
    @property
    def native_value(self):
        """Return the temperature."""
        if not self.available:
            return None
            
        temp_str = self.coordinator.data["forecast"].get("currentTemprature", "")
        if not temp_str:
            return None
            
        # Extract numeric value from string like "18.2°C"
        try:
            return float(temp_str.replace("°C", ""))
        except (ValueError, TypeError):
            return None
            
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.available:
            return {}
            
        forecast = self.coordinator.data["forecast"]
        return {
            ATTR_ISSUE_TIME: forecast.get("issuetime"),
            ATTR_FORECAST_DATE: forecast.get("forecastDate"),
            "temperature_f": forecast.get("currentTempratureFahrenheit", "").replace("°F", "")
        }


class JerseyWindDirectionSensor(JerseyWeatherSensorBase):
    """Sensor for wind direction."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "wind_direction")
        self._attr_name = "Wind Direction"
        
    @property
    def native_value(self):
        """Return the wind direction."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return self.coordinator.data["forecast"]["forecastDay"][0].get("windDirection")
        except (KeyError, IndexError):
            return None


class JerseyWindSpeedSensor(JerseyWeatherSensorBase):
    """Sensor for wind speed."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "wind_speed")
        self._attr_name = "Wind Speed"
        self._attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
        
    @property
    def native_value(self):
        """Return the wind speed."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return float(self.coordinator.data["forecast"]["forecastDay"][0].get("windSpeedKM", 0))
        except (KeyError, IndexError, ValueError):
            return None
            
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.available:
            return {}
            
        try:
            today = self.coordinator.data["forecast"]["forecastDay"][0]
            return {
                ATTR_WIND_DIRECTION: today.get("windDirection"),
                ATTR_WIND_SPEED: today.get("windSpeed"),
                ATTR_WIND_SPEED_MPH: today.get("windSpeedMPH"),
                ATTR_WIND_SPEED_KNOTS: today.get("windSpeedKnots")
            }
        except (KeyError, IndexError):
            return {}


class JerseyUVIndexSensor(JerseyWeatherSensorBase):
    """Sensor for UV index."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "uv_index")
        self._attr_name = "UV Index"
        
    @property
    def native_value(self):
        """Return the UV index."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return int(self.coordinator.data["forecast"]["forecastDay"][0].get("uvIndex", 0))
        except (KeyError, IndexError, ValueError):
            return None


class JerseyWeatherConditionSensor(JerseyWeatherSensorBase):
    """Sensor for weather condition."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "weather_condition")
        self._attr_name = "Weather Condition"
        
    @property
    def native_value(self):
        """Return the weather condition."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return self.coordinator.data["forecast"]["forecastDay"][0].get("summary")
        except (KeyError, IndexError):
            return None
            
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.available:
            return {}
            
        try:
            today = self.coordinator.data["forecast"]["forecastDay"][0]
            return {
                "morning_description": today.get("morningDescripiton"),
                "afternoon_description": today.get("afternoonDescripiton"),
                "night_description": today.get("nightDescripiton"),
                ATTR_RAIN_PROBABILITY: {
                    "morning": today.get("rainProbMorning"),
                    "afternoon": today.get("rainProbAfternoon"),
                    "evening": today.get("rainProbEvening"),
                }
            }
        except (KeyError, IndexError):
            return {}


class JerseySunriseSensor(JerseyWeatherSensorBase):
    """Sensor for sunrise time."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "sunrise")
        self._attr_name = "Sunrise"
        
    @property
    def native_value(self):
        """Return the sunrise time."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return self.coordinator.data["forecast"]["forecastDay"][0].get("sunRise")
        except (KeyError, IndexError):
            return None


class JerseySunsetSensor(JerseyWeatherSensorBase):
    """Sensor for sunset time."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "sunset")
        self._attr_name = "Sunset"
        
    @property
    def native_value(self):
        """Return the sunset time."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return self.coordinator.data["forecast"]["forecastDay"][0].get("sunSet")
        except (KeyError, IndexError):
            return None


class JerseyTideSensor(JerseyWeatherSensorBase):
    """Sensor for tide information."""

    def __init__(self, coordinator, index):
        """Initialize the sensor."""
        super().__init__(coordinator, f"tide_{index}")
        self._index = index
        self._attr_name = f"Tide {index + 1}"
        
    @property
    def native_value(self):
        """Return the tide type (high/low)."""
        if not self.coordinator.data or "tide" not in self.coordinator.data:
            return None
            
        try:
            # Get today's tides (first in the list)
            return self.coordinator.data["tide"][0]["TideTimes"][self._index].get("highLow")
        except (KeyError, IndexError):
            return None
            
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data or "tide" not in self.coordinator.data:
            return {}
            
        try:
            tide_info = self.coordinator.data["tide"][0]["TideTimes"][self._index]
            return {
                "time": tide_info.get("Time"),
                "height_m": tide_info.get("Height"),
                "height_ft": tide_info.get("HeightinFeet"),
                "date": self.coordinator.data["tide"][0].get("formattedDate")
            }
        except (KeyError, IndexError):
            return {}
