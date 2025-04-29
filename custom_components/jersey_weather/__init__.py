"""The Jersey Weather integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# List of platforms to support. There should be a matching .py file for each.
PLATFORMS = ["sensor", "weather", "camera"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Jersey Weather from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create update coordinator
    coordinator = JerseyWeatherCoordinator(hass)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
        
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unloaded

class JerseyWeatherCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Jersey Weather data."""

    def __init__(self, hass):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )
        self.api = JerseyWeatherAPI()

    async def _async_update_data(self):
        """Update data via API."""
        try:
            async with async_timeout.timeout(30):
                return await self.api.async_get_data()
        except Exception as error:
            raise UpdateFailed(f"Error communicating with API: {error}")

class JerseyWeatherAPI:
    """Jersey Weather API class."""
    
    async def async_get_data(self):
        """Get data from the API."""
        import aiohttp
        
        data = {}
        
        async with aiohttp.ClientSession() as session:
            # Fetch forecast data
            try:
                async with session.get(
                    "https://prodgojweatherstorage.blob.core.windows.net/data/jerseyForecast.json"
                ) as resp:
                    if resp.status == 200:
                        data["forecast"] = await resp.json()
                    else:
                        _LOGGER.error(f"Failed to fetch forecast data: {resp.status}")
            except Exception as error:
                _LOGGER.error(f"Error fetching forecast data: {error}")
                
            # Fetch tide data
            try:
                async with session.get(
                    "https://prodgojweatherstorage.blob.core.windows.net/data/JerseyTide5Day.json"
                ) as resp:
                    if resp.status == 200:
                        data["tide"] = await resp.json()
                    else:
                        _LOGGER.error(f"Failed to fetch tide data: {resp.status}")
            except Exception as error:
                _LOGGER.error(f"Error fetching tide data: {error}")
                
        return data
