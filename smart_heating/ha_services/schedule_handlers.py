"""Schedule service handlers for Smart Heating."""

import logging
import uuid

from homeassistant.core import ServiceCall

from ..area_manager import AreaManager
from ..const import (
    ATTR_AREA_ID,
    ATTR_DAYS,
    ATTR_NIGHT_BOOST_ENABLED,
    ATTR_NIGHT_BOOST_END_TIME,
    ATTR_NIGHT_BOOST_OFFSET,
    ATTR_NIGHT_BOOST_START_TIME,
    ATTR_SCHEDULE_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
)
from ..coordinator import SmartHeatingCoordinator
from ..models import Schedule

_LOGGER = logging.getLogger(__name__)


async def async_handle_add_schedule(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the add_schedule service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    schedule_id = call.data[ATTR_SCHEDULE_ID]
    time_str = call.data[ATTR_TIME]
    temperature = call.data[ATTR_TEMPERATURE]
    days = call.data.get(ATTR_DAYS)

    _LOGGER.debug(
        "Adding schedule %s to area %s: %s @ %.1f°C", schedule_id, area_id, time_str, temperature
    )

    try:
        area_manager.add_schedule_to_area(area_id, schedule_id, time_str, temperature, days)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Added schedule %s to area %s", schedule_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to add schedule: %s", err)


async def async_handle_remove_schedule(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the remove_schedule service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    schedule_id = call.data[ATTR_SCHEDULE_ID]

    _LOGGER.debug("Removing schedule %s from area %s", schedule_id, area_id)

    try:
        area_manager.remove_schedule_from_area(area_id, schedule_id)
        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Removed schedule %s from area %s", schedule_id, area_id)
    except ValueError as err:
        _LOGGER.error("Failed to remove schedule: %s", err)


async def async_handle_enable_schedule(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the enable_schedule service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    schedule_id = call.data[ATTR_SCHEDULE_ID]

    _LOGGER.debug("Enabling schedule %s in area %s", schedule_id, area_id)

    try:
        area = area_manager.get_area(area_id)
        if area and schedule_id in area.schedules:
            area.schedules[schedule_id].enabled = True
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Enabled schedule %s in area %s", schedule_id, area_id)
        else:
            raise ValueError(f"Schedule {schedule_id} not found in area {area_id}")
    except ValueError as err:
        _LOGGER.error("Failed to enable schedule: %s", err)


async def async_handle_disable_schedule(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the disable_schedule service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    schedule_id = call.data[ATTR_SCHEDULE_ID]

    _LOGGER.debug("Disabling schedule %s in area %s", schedule_id, area_id)

    try:
        area = area_manager.get_area(area_id)
        if area and schedule_id in area.schedules:
            area.schedules[schedule_id].enabled = False
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Disabled schedule %s in area %s", schedule_id, area_id)
        else:
            raise ValueError(f"Schedule {schedule_id} not found in area {area_id}")
    except ValueError as err:
        _LOGGER.error("Failed to disable schedule: %s", err)


async def async_handle_set_night_boost(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the set_night_boost service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    area_id = call.data[ATTR_AREA_ID]
    enabled = call.data.get(ATTR_NIGHT_BOOST_ENABLED)
    offset = call.data.get(ATTR_NIGHT_BOOST_OFFSET)
    start_time = call.data.get(ATTR_NIGHT_BOOST_START_TIME)
    end_time = call.data.get(ATTR_NIGHT_BOOST_END_TIME)
    smart_enabled = call.data.get("smart_night_boost_enabled")
    smart_target_time = call.data.get("smart_night_boost_target_time")
    weather_entity_id = call.data.get("weather_entity_id")

    _LOGGER.debug(
        "Setting night boost for area %s: enabled=%s, offset=%s, start=%s, end=%s, smart=%s",
        area_id,
        enabled,
        offset,
        start_time,
        end_time,
        smart_enabled,
    )

    try:
        area = area_manager.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")

        # Manual night boost settings
        if enabled is not None:
            area.night_boost_enabled = enabled
        if offset is not None:
            area.night_boost_offset = offset
        if start_time is not None:
            area.night_boost_start_time = start_time
        if end_time is not None:
            area.night_boost_end_time = end_time

        # Smart night boost settings
        if smart_enabled is not None:
            area.smart_night_boost_enabled = smart_enabled
        if smart_target_time is not None:
            area.smart_night_boost_target_time = smart_target_time
        if weather_entity_id is not None:
            area.weather_entity_id = weather_entity_id

        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Updated night boost for area %s", area_id)
    except ValueError as err:
        _LOGGER.error("Failed to set night boost: %s", err)


async def async_handle_copy_schedule(
    call: ServiceCall, area_manager: AreaManager, coordinator: SmartHeatingCoordinator
) -> None:
    """Handle the copy_schedule service call.

    Args:
        call: Service call data
        area_manager: Area manager instance
        coordinator: Data coordinator instance
    """
    source_area_id = call.data["source_area_id"]
    source_schedule_id = call.data["source_schedule_id"]
    target_area_id = call.data["target_area_id"]
    target_days = call.data.get("target_days", [])

    _LOGGER.debug(
        "Copying schedule %s from area %s to area %s",
        source_schedule_id,
        source_area_id,
        target_area_id,
    )

    source_area = area_manager.get_area(source_area_id)
    target_area = area_manager.get_area(target_area_id)

    if not source_area:
        _LOGGER.error("Source area %s not found", source_area_id)
        return
    if not target_area:
        _LOGGER.error("Target area %s not found", target_area_id)
        return

    try:
        source_schedule = source_area.schedules.get(source_schedule_id)
        if not source_schedule:
            _LOGGER.error("Schedule %s not found in area %s", source_schedule_id, source_area_id)
            return

        # Create new schedule(s) for target days
        if target_days:
            for day in target_days:
                new_schedule = Schedule(
                    schedule_id=f"{day.lower()}_{uuid.uuid4().hex[:8]}",
                    time=source_schedule.start_time,
                    temperature=source_schedule.temperature,
                    day=day,
                    start_time=source_schedule.start_time,
                    end_time=source_schedule.end_time,
                    enabled=source_schedule.enabled,
                )
                target_area.add_schedule(new_schedule)
        else:
            # Copy with same days
            new_schedule = Schedule(
                schedule_id=f"copied_{uuid.uuid4().hex[:8]}",
                time=source_schedule.start_time,
                temperature=source_schedule.temperature,
                day=source_schedule.day,
                start_time=source_schedule.start_time,
                end_time=source_schedule.end_time,
                enabled=source_schedule.enabled,
            )
            target_area.add_schedule(new_schedule)

        await area_manager.async_save()
        await coordinator.async_request_refresh()
        _LOGGER.info("Copied schedule from area %s to area %s", source_area_id, target_area_id)
    except Exception as err:
        _LOGGER.error("Failed to copy schedule: %s", err)
