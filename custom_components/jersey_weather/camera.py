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
    RADAR_URL_FORMAT,
    RADAR_ZOOM_URL_FORMAT,
    SATELLITE_URL_FORMAT,
    WIND_WAVES_IMAGE_URL,
    SEA_STATE_AM_IMAGE_URL,
    SEA_STATE_PM_IMAGE_URL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jersey Weather camera entities based on config entry."""
    cameras = [
        JerseyWeatherRadarCamera(hass, "radar", "Radar", RADAR_URL_FORMAT),
        JerseyWeatherRadarCamera(hass, "radar_zoom", "Radar Zoom", RADAR_ZOOM_URL_FORMAT),
        JerseyWeatherRadarCamera(hass, "satellite", "Satellite", SATELLITE_URL_FORMAT),
        JerseyWeatherStaticCamera(
            hass, "wind_waves", "Jersey Wind Waves", WIND_WAVES_IMAGE_URL
        ),
        JerseyWeatherStaticCamera(
            hass, "sea_state_am", "Jersey Sea State AM", SEA_STATE_AM_IMAGE_URL
        ),
        JerseyWeatherStaticCamera(
            hass, "sea_state_pm", "Jersey Sea State PM", SEA_STATE_PM_IMAGE_URL
        ),
    ]
    async_add_entities(cameras)


class JerseyWeatherBaseCamera(Camera):
    """Base class for Jersey Weather cameras."""

    def __init__(self, hass: HomeAssistant, camera_id: str, name: str) -> None:
        """Initialize the base camera."""
        super().__init__()
        self.hass = hass
        self._camera_id = camera_id
        self._attr_unique_id = f"jersey_weather_camera_{self._camera_id}"
        self._attr_name = name
        self._attr_has_entity_name = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "jersey_weather")},
            "name": "Jersey Weather",
            "manufacturer": "Jersey Met",
            "model": "Weather API",
            "sw_version": "1.0",
        }


class JerseyWeatherStaticCamera(JerseyWeatherBaseCamera):
    """Implementation of a Jersey Weather static camera."""

    def __init__(self, hass: HomeAssistant, camera_id: str, name: str, image_url: str) -> None:
        """Initialize the static camera."""
        super().__init__(hass, camera_id, name)
        self._image_url = image_url

    _attr_content_type = "image/jpeg"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the camera image."""
        if not self._image_url:
            _LOGGER.error("No image URL configured for %s", self.entity_id)
            return None
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(self._image_url) as resp:
                if resp.status == 200:
                    return await resp.read()
                _LOGGER.error("Failed to fetch camera image from %s: %s", self._image_url, resp.status)
        except Exception as e:
            _LOGGER.error("Error getting camera image for %s: %s", self.entity_id, e)
        return None


class JerseyWeatherRadarCamera(JerseyWeatherBaseCamera):
    """Implementation of a Jersey Weather radar camera."""

    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(
        self, hass: HomeAssistant, camera_id: str, name: str, url_format: str
    ) -> None:
        """Initialize the radar camera."""
        super().__init__(hass, camera_id, name)
        self._url_format = url_format

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        return "Idle"
    _attr_content_type = "image/gif"

    async def stream_source(self) -> str | None:
        """Return the source of the stream for the radar camera."""
        return f"/api/camera_proxy_stream/{self.entity_id}"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Fetch radar images and create an animated GIF."""
        image_urls = [self._url_format.format(i) for i in range(1, 11)]

        async def fetch_image(session, url):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    _LOGGER.warning("Failed to fetch %s: %s", url, response.status)
            except aiohttp.ClientError as e:
                _LOGGER.warning(f"Failed to fetch {url}: {e}")
            return None

        session = async_get_clientsession(self.hass)
        tasks = [fetch_image(session, url) for url in image_urls]
        image_data = await asyncio.gather(*tasks)

        images = [Image.open(io.BytesIO(data)) for data in image_data if data]

        if not images:
            _LOGGER.error("Could not download any radar images to generate GIF.")
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
        return buffer.getvalue()
