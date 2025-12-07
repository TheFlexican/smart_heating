"""System service handlers for Smart Heating."""

import logging
from homeassistant.core import ServiceCall

from ..coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_refresh(call: ServiceCall, coordinator: SmartHeatingCoordinator) -> None:
    """Handle the refresh service call.
    
    Args:
        call: Service call data
        coordinator: Data coordinator instance
    """
    _LOGGER.debug("Refresh service called")
    await coordinator.async_request_refresh()
    _LOGGER.info("Smart Heating data refreshed")
