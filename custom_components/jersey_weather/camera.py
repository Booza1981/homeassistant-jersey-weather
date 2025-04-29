"""Camera platform for Jersey Weather integration."""
import logging
from typing import Optional

import aiohttp
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    RADAR_IMAGE_URL,
    SATELLITE_IMAGE_URL,
    WIND_WAVES_IMAGE_URL,
    SEA_STATE_AM_IMAGE_URL,
    SEA_STATE_PM_IMAGE_URL,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jersey Weather camera entities based on config entry."""
    # Add camera entities for various images
    cameras = [
        JerseyWeatherCamera(hass, "radar", "Jersey Weather Radar", RADAR_IMAGE_URL),
        JerseyWeatherCamera(hass, "satellite", "Jersey Weather Satellite", SATELLITE_IMAGE_URL),
        JerseyWeatherCamera(hass, "wind_waves", "Jersey Wind Waves", WIND_WAVES_IMAGE_URL),
        JerseyWeatherCamera(hass, "sea_state_am", "Jersey Sea State AM", SEA_STATE_AM_IMAGE_URL),
        JerseyWeatherCamera(hass, "sea_state_pm", "Jersey Sea State PM", SEA_STATE_PM_IMAGE_URL),
    ]
    
    async_add_entities(cameras)


class JerseyWeatherCamera(Camera):
    """Implementation of a Jersey Weather camera."""

    def __init__(self, hass, camera_id, name, image_url):
        """Initialize the camera."""
        super().__init__()
        self.hass = hass
        self._attr_unique_id = f"jersey_weather_camera_{camera_id}"
        self._attr_name = name
        self._image_url = image_url
        self._attr_has_entity_name = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "jersey_weather")},
            "name": "Jersey Weather",
            "manufacturer": "Jersey Met",
            "model": "Weather API",
            "sw_version": "1.0",
        }
        self._image = None
        self._attr_is_streaming = False
        self._attr_motion_detection_enabled = False
        self._attr_is_recording = False
        
    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return image response."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._image_url) as resp:
                    if resp.status == 200:
                        self._image = await resp.read()
                        return self._image
        except Exception as error:
            _LOGGER.error(f"Error getting camera image: {error}")
            
        return self._image
