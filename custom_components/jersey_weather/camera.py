"""Camera platform for Jersey Weather integration."""
import logging
from typing import Optional
import asyncio
import io
import aiohttp
from PIL import Image

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
        JerseyWeatherCamera(hass, "radar", "Radar", RADAR_IMAGE_URL),
        JerseyWeatherCamera(hass, "satellite", "Satellite", SATELLITE_IMAGE_URL),
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
        if camera_id == "radar":
            self._attr_supported_features = CameraEntityFeature.STREAM

    @property
    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        if self._attr_unique_id == "jersey_weather_camera_radar":
            return f"/api/camera_proxy_stream/{self.entity_id}"
        return None

    @property
    def content_type(self) -> str:
        """Return the content type of the image."""
        if self._attr_unique_id == "jersey_weather_camera_radar":
            return "image/gif"
        return "image/jpeg"
        
    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return image response."""
        if self._attr_unique_id != "jersey_weather_camera_radar":
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(self._image_url) as resp:
                    if resp.status == 200:
                        self._image = await resp.read()
                        return self._image
                    else:
                        _LOGGER.error("Failed to fetch camera image: %s", resp.status)
            except Exception as error:
                _LOGGER.error("Error getting camera image: %s", error)
            return self._image

        # Animated GIF logic for radar
        image_urls = [f"https://sojpublicdata.blob.core.windows.net/jerseymet/Radar{i:02d}.JPG" for i in range(1, 11)]
        
        async def fetch_image(session, url):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
            except aiohttp.ClientError as e:
                _LOGGER.warning(f"Failed to fetch {url}: {e}")
            return None

        session = async_get_clientsession(self.hass)
        tasks = [fetch_image(session, url) for url in image_urls]
        image_data = await asyncio.gather(*tasks)
        
        images = [Image.open(io.BytesIO(data)) for data in image_data if data]
        
        if not images:
            _LOGGER.error("Could not download any radar images.")
            return None
            
        buffer = io.BytesIO()
        images[0].save(
            buffer,
            format='GIF',
            save_all=True,
            append_images=images[1:],
            duration=500,
            loop=0
        )
        gif_bytes = buffer.getvalue()
        _LOGGER.info(f"Generated GIF bytes (first 10): {gif_bytes[:10]}")
        return gif_bytes
