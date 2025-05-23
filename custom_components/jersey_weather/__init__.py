"""The Jersey Weather integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN, 
    FORECAST_URL, 
    TIDE_URL, 
    COASTAL_REPORTS_URL,
    SHIPPING_FORECAST_URL,
)

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
    
    # Set up platforms using the new recommended method
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Use the newer method for unloading platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unload_ok

class JerseyWeatherCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Jersey Weather data."""

    def __init__(self, hass):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),
        )
        self.hass = hass

    async def _async_update_data(self):
        """Update data via API."""
        try:
            async with async_timeout.timeout(30):
                return await self._get_data()
        except Exception as error:
            _LOGGER.error("Error communicating with API: %s", error)
            raise UpdateFailed(f"Error communicating with API: {error}")
            
    async def _get_data(self):
        """Get data from the API."""
        session = async_get_clientsession(self.hass)
        data = {}
        
        # Fetch forecast data
        try:
            async with session.get(FORECAST_URL) as resp:
                if resp.status == 200:
                    data["forecast"] = await resp.json()
                    _LOGGER.debug("Successfully fetched forecast data")
                else:
                    _LOGGER.error("Failed to fetch forecast data: %s", resp.status)
        except Exception as error:
            _LOGGER.error("Error fetching forecast data: %s", error)
            
        # Fetch tide data
        try:
            async with session.get(TIDE_URL) as resp:
                if resp.status == 200:
                    data["tide"] = await resp.json()
                    _LOGGER.debug("Successfully fetched tide data")
                else:
                    _LOGGER.error("Failed to fetch tide data: %s", resp.status)
        except Exception as error:
            _LOGGER.error("Error fetching tide data: %s", error)
            
        # Fetch coastal reports data
        try:
            async with session.get(COASTAL_REPORTS_URL) as resp:
                if resp.status == 200:
                    data["coastal"] = await resp.json()
                    _LOGGER.debug("Successfully fetched coastal data")
                else:
                    _LOGGER.error("Failed to fetch coastal data: %s", resp.status)
        except Exception as error:
            _LOGGER.error("Error fetching coastal data: %s", error)
            
        # Fetch shipping forecast data
        try:
            async with session.get(SHIPPING_FORECAST_URL) as resp:
                if resp.status == 200:
                    data["shipping"] = await resp.json()
                    _LOGGER.debug("Successfully fetched shipping data")
                else:
                    _LOGGER.error("Failed to fetch shipping data: %s", resp.status)
        except Exception as error:
            _LOGGER.error("Error fetching shipping data: %s", error)
        
        _LOGGER.debug("Data keys: %s", data.keys())
        if "forecast" in data:
            _LOGGER.debug("Forecast data contains: %s", data["forecast"].keys())
            
        return data