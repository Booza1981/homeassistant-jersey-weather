"""Sensor platform for Jersey Weather integration."""
import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfPressure,
    PERCENTAGE,
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
    ATTR_PRESSURE,
    ATTR_PRESSURE_TENDENCY,
    ATTR_SEA_TEMPERATURE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jersey Weather sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    _LOGGER.debug("Setting up sensors with coordinator data: %s", 
                  "available" if coordinator.data else "not available")
    
    sensors = []
    
    # Current Weather Sensors
    sensors.append(JerseyCurrentTemperatureSensor(coordinator))
    # Forecast Temp Sensors for today and tomorrow
    for i in range(2):  # 0 = today, 1 = tomorrow
        sensors.append(JerseyForecastTempSensor(coordinator, i, "min"))
        sensors.append(JerseyForecastTempSensor(coordinator, i, "max"))

    sensors.append(JerseyWindDirectionSensor(coordinator))
    sensors.append(JerseyWindSpeedSensor(coordinator))
    sensors.append(JerseyUVIndexSensor(coordinator))
    sensors.append(JerseyWeatherConditionSensor(coordinator))
    sensors.append(JerseySunriseSensor(coordinator))
    sensors.append(JerseySunsetSensor(coordinator))
    
    # Additional sensors for enhanced weather data
    sensors.append(JerseyRainProbabilitySensor(coordinator))
    
    # New sensors for coastal and shipping data
    sensors.append(JerseyAirportPressureSensor(coordinator))
    sensors.append(JerseySeaTemperatureSensor(coordinator))
    
    # Tide Sensors - we'll create sensors for today's tides  
    sensors.append(JerseyTideSummarySensor(coordinator))

    _LOGGER.debug("Adding %d sensors", len(sensors))
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
        return "forecast" in self.coordinator.data


class JerseyCurrentTemperatureSensor(JerseyWeatherSensorBase):
    """Sensor for current temperature."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "current_temperature")
        self._attr_name = "Current Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
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
            _LOGGER.error("Error parsing temperature: %s", temp_str)
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

class JerseyForecastTempSensor(JerseyWeatherSensorBase):
    """Sensor for min/max forecast temperatures for days 1–4."""

    def __init__(self, coordinator, day_index: int, temp_type: str):
        key = f"day{day_index+1}_{temp_type}_temp"
        super().__init__(coordinator, key)
        self._day_index = day_index
        self._temp_type = temp_type  # "min" or "max"
        if day_index == 0:
            label = "Today"
        elif day_index == 1:
            label = "Tomorrow"
        else:
            label = f"Day {day_index+1}"

        self._attr_name = f"{label} {temp_type.capitalize()} Temp"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        try:
            forecast_days = self.coordinator.data["forecast"]["forecastDay"]
            if self._day_index >= len(forecast_days):
                return None

            temp_key = "maxTemp" if self._temp_type == "max" else "minTemp"
            temp_str = forecast_days[self._day_index].get(temp_key, "").replace("°C", "").strip()

            if not temp_str:
                return None
            return float(temp_str)

        except Exception as e:
            _LOGGER.error("Error getting forecast temperature: %s", e)
            return None


class JerseyWindDirectionSensor(JerseyWeatherSensorBase):
    """Sensor for wind direction."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "wind_direction")
        self._attr_name = "Wind Direction"
        self._attr_icon = "mdi:weather-windy"
        
    @property
    def native_value(self):
        """Return the wind direction."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return self.coordinator.data["forecast"]["forecastDay"][0].get("windDirection")
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting wind direction: %s", e)
            return None


class JerseyWindSpeedSensor(JerseyWeatherSensorBase):
    """Sensor for wind speed."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "wind_speed")
        self._attr_name = "Wind Speed"
        self._attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
        self._attr_device_class = SensorDeviceClass.WIND_SPEED
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
    @property
    def native_value(self):
        """Return the wind speed."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return float(self.coordinator.data["forecast"]["forecastDay"][0].get("windSpeedKM", 0))
        except (KeyError, IndexError, ValueError) as e:
            _LOGGER.error("Error getting wind speed: %s", e)
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
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting wind speed attributes: %s", e)
            return {}


class JerseyUVIndexSensor(JerseyWeatherSensorBase):
    """Sensor for UV index."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "uv_index")
        self._attr_name = "UV Index"
        self._attr_icon = "mdi:weather-sunny-alert"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
    @property
    def native_value(self):
        """Return the UV index."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return int(self.coordinator.data["forecast"]["forecastDay"][0].get("uvIndex", 0))
        except (KeyError, IndexError, ValueError) as e:
            _LOGGER.error("Error getting UV index: %s", e)
            return None


class JerseyRainProbabilitySensor(JerseyWeatherSensorBase):
    """Sensor for rain probability."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "rain_probability")
        self._attr_name = "Rain Probability"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:water-percent"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
    @property
    def native_value(self):
        """Return the maximum rain probability for the day."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            today = self.coordinator.data["forecast"]["forecastDay"][0]
            # Get the maximum probability among morning, afternoon, and evening
            probs = [
                int(today.get("rainProbMorning", 0) or 0),
                int(today.get("rainProbAfternoon", 0) or 0),
                int(today.get("rainProbEvening", 0) or 0)
            ]
            return max(probs)
        except (KeyError, IndexError, ValueError) as e:
            _LOGGER.error("Error getting rain probability: %s", e)
            return 0
            
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.available:
            return {}
            
        try:
            # Get attributes for today (for backward compatibility)
            today = self.coordinator.data["forecast"]["forecastDay"][0]
            today_probs = {
                "morning": int(today.get("rainProbMorning", 0) or 0),
                "afternoon": int(today.get("rainProbAfternoon", 0) or 0),
                "evening": int(today.get("rainProbEvening", 0) or 0)
            }
            
            # Calculate today's average
            today_avg = round(sum(today_probs.values()) / len(today_probs))
            
            # Create attributes dictionary with today's values at the top level for compatibility
            attributes = {
                "morning": today_probs["morning"],
                "afternoon": today_probs["afternoon"],
                "evening": today_probs["evening"],
                "max": max(today_probs.values()),
                "average": today_avg
            }
            
            # Add daily averages for all forecast days
            forecast_days = self.coordinator.data["forecast"]["forecastDay"]
            for day in forecast_days:
                day_name = day.get("dayName", "")
                if not day_name:
                    continue
                    
                # Calculate average probability for this day
                day_probs = {
                    "morning": int(day.get("rainProbMorning", 0) or 0),
                    "afternoon": int(day.get("rainProbAfternoon", 0) or 0),
                    "evening": int(day.get("rainProbEvening", 0) or 0)
                }
                
                day_avg = round(sum(day_probs.values()) / len(day_probs))
                
                # Add to attributes with detailed breakdown
                attributes[day_name] = {
                    "morning": day_probs["morning"],
                    "afternoon": day_probs["afternoon"],
                    "evening": day_probs["evening"],
                    "max": max(day_probs.values()),
                    "average": day_avg
                }
            
            return attributes
            
        except (KeyError, IndexError, ValueError) as e:
            _LOGGER.error("Error getting rain probability attributes: %s", e)
            return {}


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
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting weather condition: %s", e)
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
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting weather condition attributes: %s", e)
            return {}


class JerseySunriseSensor(JerseyWeatherSensorBase):
    """Sensor for sunrise time."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "sunrise")
        self._attr_name = "Sunrise"
        self._attr_icon = "mdi:weather-sunset-up"
        
    @property
    def native_value(self):
        """Return the sunrise time."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return self.coordinator.data["forecast"]["forecastDay"][0].get("sunRise")
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting sunrise: %s", e)
            return None


class JerseySunsetSensor(JerseyWeatherSensorBase):
    """Sensor for sunset time."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "sunset")
        self._attr_name = "Sunset"
        self._attr_icon = "mdi:weather-sunset-down"
        
    @property
    def native_value(self):
        """Return the sunset time."""
        if not self.available:
            return None
            
        try:
            # Get today's forecast (first in the list)
            return self.coordinator.data["forecast"]["forecastDay"][0].get("sunSet")
        except (KeyError, IndexError) as e:
            _LOGGER.error("Error getting sunset: %s", e)
            return None
        
class JerseyTideSummarySensor(JerseyWeatherSensorBase):
    """Sensor for a compact summary of today's tides."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "tide_summary")
        self._attr_name = "Tide Summary"
        self._attr_icon = "mdi:wave"

    @property
    def native_value(self):
        """Return a formatted string like '05:12 High, 11:26 Low, ...'"""
        if not self.coordinator.data or "tide" not in self.coordinator.data:
            return None

        try:
            tide_events = self.coordinator.data.get("tide", [{}])[0].get("TideTimes", [])
            return ", ".join(
                f"{event.get('Time')} {event.get('highLow')}"
                for event in tide_events[:4]
            )
        except Exception as e:
            _LOGGER.error("Error getting tide summary: %s", e)
            return None

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data or "tide" not in self.coordinator.data:
            return {}
        try:
            return {
                "date": self.coordinator.data["tide"][0].get("formattedDate")
            }
        except Exception:
            return {}



class JerseyAirportPressureSensor(JerseyWeatherSensorBase):
    """Sensor for Jersey Airport pressure."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "airport_pressure")
        self._attr_name = "Jersey Airport Pressure"
        self._attr_native_unit_of_measurement = UnitOfPressure.HPA
        self._attr_device_class = SensorDeviceClass.PRESSURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:gauge"
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.data:
            return False
        return "coastal" in self.coordinator.data
        
    @property
    def native_value(self):
        """Return the pressure value."""
        if not self.available:
            return None
            
        try:
            # Find Jersey Airport in the station reports
            stations = self.coordinator.data["coastal"].get("StationReport", [])
            for station in stations:
                if station.get("Name") == "Jersey Airport":
                    # Convert pressure string to number
                    pressure_str = station.get("Pressure", "")
                    if pressure_str:
                        try:
                            return float(pressure_str)
                        except ValueError:
                            _LOGGER.error("Error parsing pressure value: %s", pressure_str)
                    break
            return None
        except (KeyError, ValueError) as e:
            _LOGGER.error("Error getting airport pressure: %s", e)
            return None
            
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.available:
            return {}
            
        try:
            stations = self.coordinator.data["coastal"].get("StationReport", [])
            for station in stations:
                if station.get("Name") == "Jersey Airport":
                    return {
                        "wind": station.get("Wind", ""),
                        "visibility": station.get("Visibility", ""),
                        "weather": station.get("Weather", ""),
                        ATTR_PRESSURE_TENDENCY: station.get("Tendency", ""),
                        "updated": self.coordinator.data["coastal"].get("Date", "") + " " + 
                                   self.coordinator.data["coastal"].get("Time", "")
                    }
            return {}
        except (KeyError) as e:
            _LOGGER.error("Error getting airport pressure attributes: %s", e)
            return {}


class JerseySeaTemperatureSensor(JerseyWeatherSensorBase):
    """Sensor for sea temperature."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "sea_temperature")
        self._attr_name = "Sea Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:waves"
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.data:
            return False
        return "shipping" in self.coordinator.data
        
    @property
    def native_value(self):
        """Return the sea temperature."""
        if not self.available:
            return None
            
        try:
            # Extract the sea temperature from shipping data
            temp_str = self.coordinator.data["shipping"].get("seatempToday", "")
            if not temp_str:
                return None
                
            # Extract numeric value from string like "12.2°C"
            try:
                return float(temp_str.replace("°C", ""))
            except (ValueError, TypeError):
                _LOGGER.error("Error parsing sea temperature: %s", temp_str)
                return None
        except (KeyError) as e:
            _LOGGER.error("Error getting sea temperature: %s", e)
            return None
            
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.available:
            return {}
            
        try:
            shipping = self.coordinator.data["shipping"]
            return {
                "wind_description": shipping.get("winddescToday", ""),
                "sea_state": shipping.get("seastateToday", ""),
                "weather": shipping.get("weatherToday", ""),
                "visibility": shipping.get("visibilityToday", ""),
                "issued_at": shipping.get("Issued", ""),
                "forecast_date": shipping.get("Date", "")
            }
        except (KeyError) as e:
            _LOGGER.error("Error getting sea temperature attributes: %s", e)
            return {}
