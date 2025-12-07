"""Sensor service handlers for Smart Heating."""

import logging
from homeassistant.core import ServiceCall

from ..area_manager import AreaManager
from ..const import ATTR_AREA_ID
from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)

# Error message constants
ERROR_AREA_NOT_FOUND = "Area %s not found"


async def async_handle_add_window_sensor(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the add_window_sensor service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    entity_id = call.data["entity_id"]
    
    _LOGGER.debug("Adding window sensor %s to area %s", entity_id, area_id)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error(ERROR_AREA_NOT_FOUND, area_id)
        return
    
    try:
        area.add_window_sensor(entity_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Added window sensor %s to area %s", entity_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to add window sensor: %s", err)


async def async_handle_remove_window_sensor(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the remove_window_sensor service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    entity_id = call.data["entity_id"]
    
    _LOGGER.debug("Removing window sensor %s from area %s", entity_id, area_id)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error(ERROR_AREA_NOT_FOUND, area_id)
        return
    
    try:
        area.remove_window_sensor(entity_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Removed window sensor %s from area %s", entity_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to remove window sensor: %s", err)


async def async_handle_add_presence_sensor(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the add_presence_sensor service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    entity_id = call.data["entity_id"]
    
    _LOGGER.debug("Adding presence sensor %s to area %s", entity_id, area_id)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error(ERROR_AREA_NOT_FOUND, area_id)
        return
    
    try:
        area.add_presence_sensor(entity_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Added presence sensor %s to area %s", entity_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to add presence sensor: %s", err)


async def async_handle_remove_presence_sensor(
    call: ServiceCall, 
    area_manager: AreaManager, 
    coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the remove_presence_sensor service call.
    
    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    entity_id = call.data["entity_id"]
    
    _LOGGER.debug("Removing presence sensor %s from area %s", entity_id, area_id)
    
    area = area_manager.get_area(area_id)
    if not area:
        _LOGGER.error(ERROR_AREA_NOT_FOUND, area_id)
        return
    
    try:
        area.remove_presence_sensor(entity_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Removed presence sensor %s from area %s", entity_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to remove presence sensor: %s", err)
