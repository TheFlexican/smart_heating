"""Vacation mode service handlers for Smart Heating."""

import logging
from homeassistant.core import HomeAssistant, ServiceCall

from ..const import DOMAIN
from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_enable_vacation_mode(
    call: ServiceCall,
    hass: HomeAssistant,
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle enable_vacation_mode service.
    
    Args:
        call: Service call data
        hass: Home Assistant instance
        coordinator: Data coordinator instance
    """
    start_date = call.data.get("start_date")
    end_date = call.data.get("end_date")
    preset_mode = call.data.get("preset_mode", "away")
    frost_protection = call.data.get("frost_protection_override", True)
    min_temp = call.data.get("min_temperature", 10.0)
    auto_disable = call.data.get("auto_disable", True)
    
    try:
        vacation_manager = hass.data.get(DOMAIN, {}).get("vacation_manager")
        if not vacation_manager:
            _LOGGER.error("Vacation manager not available")
            return
        
        await vacation_manager.async_enable(
            start_date=start_date,
            end_date=end_date,
            preset_mode=preset_mode,
            frost_protection_override=frost_protection,
            min_temperature=min_temp,
            auto_disable=auto_disable,
            person_entities=[]  # TODO: Add support for person entities in service call
        )
        
        _LOGGER.info("Vacation mode enabled: %s to %s, preset=%s", start_date, end_date, preset_mode)
    except Exception as err:
        _LOGGER.error("Failed to enable vacation mode: %s", err)


async def async_handle_disable_vacation_mode(
    call: ServiceCall,
    hass: HomeAssistant,
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle disable_vacation_mode service.
    
    Args:
        call: Service call data
        hass: Home Assistant instance
        coordinator: Data coordinator instance
    """
    try:
        vacation_manager = hass.data.get(DOMAIN, {}).get("vacation_manager")
        if not vacation_manager:
            _LOGGER.error("Vacation manager not available")
            return
        
        await vacation_manager.async_disable()
        _LOGGER.info("Vacation mode disabled")
    except Exception as err:
        _LOGGER.error("Failed to disable vacation mode: %s", err)
