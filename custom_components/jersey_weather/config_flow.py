"""Config flow for Jersey Weather integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, FORECAST_URL

_LOGGER = logging.getLogger(__name__)

class JerseyWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jersey Weather."""

    VERSION = 1
    
    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is None:
            return self.async_show_form(
                step_id="user", 
                data_schema=vol.Schema({}),
                errors=errors,
            )
            
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
            
        # Test API connection
        try:
            result = await self._test_api()
            if not result:
                errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title="Jersey Weather", data={})
            
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema({}),
            errors=errors,
        )
        
    async def _test_api(self) -> bool:
        """Test API connection."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(FORECAST_URL) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Check if we got valid data
                        if "forecastDay" in data and isinstance(data["forecastDay"], list):
                            return True
        except Exception as error:
            _LOGGER.error(f"Error connecting to API: {error}")
            return False
            
        return False
