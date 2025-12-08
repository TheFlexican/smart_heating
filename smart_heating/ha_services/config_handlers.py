"""Configuration service handlers for Smart Heating."""

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from ..area_manager import AreaManager
from ..const import (
    ATTR_FROST_PROTECTION_ENABLED,
    ATTR_FROST_PROTECTION_TEMP,
    ATTR_HISTORY_RETENTION_DAYS,
    ATTR_HYSTERESIS,
    DOMAIN,
)
from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_set_hysteresis(
    call: ServiceCall, hass: HomeAssistant, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_hysteresis service call.

    Args:
        call: Service call data
        hass: Home Assistant instance
        coordinator: Data coordinator instance
    """
    hysteresis = call.data[ATTR_HYSTERESIS]

    _LOGGER.debug("Setting global hysteresis to %.2f°C", hysteresis)

    try:
        climate_controller = hass.data[DOMAIN].get("climate_controller")
        if climate_controller:
            climate_controller._hysteresis = hysteresis
            _LOGGER.info("Set global hysteresis to %.2f°C", hysteresis)
        else:
            raise ValueError("Climate controller not found")
    except ValueError as err:
        _LOGGER.error("Failed to set hysteresis: %s", err)


async def async_handle_set_opentherm_gateway(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_opentherm_gateway service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    gateway_id = call.data.get("gateway_id")
    enabled = call.data.get("enabled", True)

    _LOGGER.debug("Setting OpenTherm gateway to %s (enabled: %s)", gateway_id, enabled)

    try:
        area_manager.set_opentherm_gateway(gateway_id, enabled)
        await area_manager.async_save()
        _LOGGER.info("Set OpenTherm gateway to %s (enabled: %s)", gateway_id, enabled)
    except ValueError as err:
        _LOGGER.error("Failed to set OpenTherm gateway: %s", err)


async def async_handle_set_trv_temperatures(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_trv_temperatures service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    heating_temp = call.data.get("heating_temp", 25.0)
    idle_temp = call.data.get("idle_temp", 10.0)
    temp_offset = call.data.get("temp_offset")

    if temp_offset is not None:
        _LOGGER.debug(
            "Setting TRV temperatures: heating=%.1f°C, idle=%.1f°C, offset=%.1f°C",
            heating_temp,
            idle_temp,
            temp_offset,
        )
    else:
        _LOGGER.debug(
            "Setting TRV temperatures: heating=%.1f°C, idle=%.1f°C", heating_temp, idle_temp
        )

    try:
        area_manager.set_trv_temperatures(heating_temp, idle_temp, temp_offset)
        await area_manager.async_save()
        if temp_offset is not None:
            _LOGGER.info(
                "Set TRV temperatures: heating=%.1f°C, idle=%.1f°C, offset=%.1f°C",
                heating_temp,
                idle_temp,
                temp_offset,
            )
        else:
            _LOGGER.info(
                "Set TRV temperatures: heating=%.1f°C, idle=%.1f°C", heating_temp, idle_temp
            )
    except ValueError as err:
        _LOGGER.error("Failed to set TRV temperatures: %s", err)


async def async_handle_set_frost_protection(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_frost_protection service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    enabled = call.data.get(ATTR_FROST_PROTECTION_ENABLED)
    temp = call.data.get(ATTR_FROST_PROTECTION_TEMP)

    _LOGGER.debug(
        "Setting frost protection: enabled=%s, temp=%.1f°C", enabled, temp if temp else 7.0
    )

    try:
        if enabled is not None:
            area_manager.frost_protection_enabled = enabled
        if temp is not None:
            area_manager.frost_protection_temp = temp

        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info(
            "Set frost protection: enabled=%s, temp=%.1f°C",
            area_manager.frost_protection_enabled,
            area_manager.frost_protection_temp,
        )
    except ValueError as err:
        _LOGGER.error("Failed to set frost protection: %s", err)


async def async_handle_set_history_retention(
    call: ServiceCall, hass: HomeAssistant, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle set_history_retention service.

    Args:
        call: Service call data
        hass: Home Assistant instance
        coordinator: Data coordinator instance
    """
    days = call.data.get(ATTR_HISTORY_RETENTION_DAYS)

    try:
        history_tracker = hass.data.get(DOMAIN, {}).get("history")
        if not history_tracker:
            _LOGGER.error("History tracker not available")
            return

        history_tracker.set_retention_days(days)
        await history_tracker.async_save()

        # Trigger immediate cleanup to remove old data if retention was reduced
        await history_tracker._async_cleanup_old_entries()

        _LOGGER.info("History retention set to %d days", days)
    except Exception as err:
        _LOGGER.error("Failed to set history retention: %s", err)
