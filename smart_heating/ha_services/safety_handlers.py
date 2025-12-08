"""Safety sensor service handlers for Smart Heating."""

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from ..area_manager import AreaManager
from ..const import DOMAIN
from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_set_safety_sensor(
    call: ServiceCall,
    hass: HomeAssistant,
    area_manager: AreaManager,
    coordinator: SmartHeatingCoordinator,
) -> None:
    """Handle set_safety_sensor service.

    Args:
        call: Service call data
        hass: Home Assistant instance
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    try:
        safety_monitor = hass.data.get(DOMAIN, {}).get("safety_monitor")

        sensor_id = call.data.get("sensor_id")
        attribute = call.data.get("attribute", "smoke")
        alert_value = call.data.get("alert_value", True)
        enabled = call.data.get("enabled", True)

        area_manager.add_safety_sensor(sensor_id, attribute, alert_value, enabled)
        await area_manager.async_save()

        # Reconfigure safety monitor to use new sensor
        if safety_monitor:
            await safety_monitor.async_reconfigure()

        _LOGGER.info(
            "Safety sensor configured: %s (attribute: %s, enabled: %s)",
            sensor_id,
            attribute,
            enabled,
        )
    except Exception as err:
        _LOGGER.error("Failed to set safety sensor: %s", err)


async def async_handle_remove_safety_sensor(
    call: ServiceCall,
    hass: HomeAssistant,
    area_manager: AreaManager,
    coordinator: SmartHeatingCoordinator,
) -> None:
    """Handle remove_safety_sensor service.

    Args:
        call: Service call data
        hass: Home Assistant instance
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    try:
        safety_monitor = hass.data.get(DOMAIN, {}).get("safety_monitor")

        sensor_id = call.data.get("sensor_id")

        area_manager.remove_safety_sensor(sensor_id)
        await area_manager.async_save()

        # Reconfigure safety monitor
        if safety_monitor:
            await safety_monitor.async_reconfigure()

        _LOGGER.info("Safety sensor removed: %s", sensor_id)
    except Exception as err:
        _LOGGER.error("Failed to remove safety sensor: %s", err)
