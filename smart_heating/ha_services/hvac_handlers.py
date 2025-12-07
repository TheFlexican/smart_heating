"""HVAC service handlers for Smart Heating."""

import logging
from homeassistant.core import ServiceCall

from ..area_manager import AreaManager
from ..const import (
    ATTR_AREA_ID,
    ATTR_PRESET_MODE,
    ATTR_BOOST_DURATION,
    ATTR_BOOST_TEMP,
    ATTR_HVAC_MODE,
)
from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_set_preset_mode(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_preset_mode service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    preset_mode = call.data[ATTR_PRESET_MODE]
    
    _LOGGER.debug("Setting preset mode for area %s to %s", area_id, preset_mode)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error("Area %s not found", area_id)
        return
    
    try:
        area.set_preset_mode(preset_mode)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Set preset mode for area %s to %s", area_id, preset_mode)
    except ValueError as err:
        _LOGGER.error("Failed to set preset mode: %s", err)


async def async_handle_set_boost_mode(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_boost_mode service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    duration = call.data.get(ATTR_BOOST_DURATION, 60)
    temp = call.data.get(ATTR_BOOST_TEMP)
    
    _LOGGER.debug("Setting boost mode for area %s: %d minutes", area_id, duration)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error("Area %s not found", area_id)
        return
    
    try:
        area.set_boost_mode(duration, temp)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Activated boost mode for area %s: %d minutes at %.1f°C", 
                    area_id, duration, area.boost_temp)
    except ValueError as err:
        _LOGGER.error("Failed to set boost mode: %s", err)


async def async_handle_cancel_boost(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the cancel_boost service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    
    _LOGGER.debug("Cancelling boost mode for area %s", area_id)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error("Area %s not found", area_id)
        return
    
    try:
        area.cancel_boost_mode()
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Cancelled boost mode for area %s", area_id)
    except ValueError as err:
        _LOGGER.error("Failed to cancel boost mode: %s", err)


async def async_handle_set_hvac_mode(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_hvac_mode service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    hvac_mode = call.data[ATTR_HVAC_MODE]
    
    _LOGGER.debug("Setting HVAC mode for area %s to %s", area_id, hvac_mode)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error("Area %s not found", area_id)
        return
    
    try:
        area.hvac_mode = hvac_mode
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Set HVAC mode for area %s to %s", area_id, hvac_mode)
    except ValueError as err:
        _LOGGER.error("Failed to set HVAC mode: %s", err)
