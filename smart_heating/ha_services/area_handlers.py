"""Area service handlers for Smart Heating."""

import logging
from homeassistant.core import ServiceCall

from ..area_manager import AreaManager
from ..const import ATTR_AREA_ID, ATTR_TEMPERATURE
from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_set_temperature(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_area_temperature service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    temperature = call.data[ATTR_TEMPERATURE]
    
    _LOGGER.debug("Setting area %s temperature to %.1f°C", area_id, temperature)
    
    try:
        area_manager.set_area_target_temperature(area_id, temperature)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Set area %s temperature to %.1f°C", area_id, temperature)
    except ValueError as err:
        _LOGGER.error("Failed to set temperature: %s", err)


async def async_handle_enable_area(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the enable_area service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    
    _LOGGER.debug("Enabling area %s", area_id)
    
    try:
        area_manager.enable_area(area_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Enabled area %s", area_id)
    except ValueError as err:
        _LOGGER.error("Failed to enable area: %s", err)


async def async_handle_disable_area(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the disable_area service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    
    _LOGGER.debug("Disabling area %s", area_id)
    
    try:
        area_manager.disable_area(area_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Disabled area %s", area_id)
    except ValueError as err:
        _LOGGER.error("Failed to disable area: %s", err)
