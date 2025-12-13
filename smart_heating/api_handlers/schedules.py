"""Schedule API handlers for Smart Heating."""

import logging
import uuid

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from ..area_manager import AreaManager
from ..const import DOMAIN
from ..models import Area, Schedule
from ..utils import get_coordinator, validate_area_id, validate_temperature

_LOGGER = logging.getLogger(__name__)


async def handle_add_schedule(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Add schedule to an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Schedule data (day, start_time, end_time, temperature or preset_mode)

    Returns:
        JSON response
    """
    # Validate area_id
    is_valid, error_msg = validate_area_id(area_id)
    if not is_valid:
        return web.json_response({"error": error_msg}, status=400)

    schedule_id = data.get("id") or str(uuid.uuid4())
    temperature = data.get("temperature")
    preset_mode = data.get("preset_mode")

    # Require either temperature or preset_mode
    if temperature is None and preset_mode is None:
        return web.json_response(
            {"error": "Either temperature or preset_mode is required"}, status=400
        )

    # Validate temperature if provided
    if temperature is not None:
        is_valid, error_msg = validate_temperature(temperature)
        if not is_valid:
            return web.json_response({"error": error_msg}, status=400)

    try:
        # Ensure area exists in storage
        if area_manager.get_area(area_id) is None:
            # Auto-create area entry for this HA area if not exists
            area_registry = ar.async_get(hass)
            ha_area = area_registry.async_get_area(area_id)
            if ha_area:
                # Create internal storage for this HA area
                area = Area(area_id, ha_area.name)
                area.area_manager = area_manager
                area_manager.areas[area_id] = area
            else:
                return web.json_response(
                    {"error": f"Area {area_id} not found"}, status=404
                )

        # Create schedule from frontend data
        # Validate required fields - accept either 'time' (legacy) or 'start_time' (new)
        time_str = data.get("time") or data.get("start_time")
        if not time_str:
            return web.json_response(
                {"error": "Missing required field: time or start_time"}, status=400
            )

        schedule = Schedule(
            schedule_id=schedule_id,
            time=time_str,
            temperature=temperature,
            days=data.get("days"),
            enabled=data.get("enabled", True),
            day=data.get("day"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            preset_mode=data.get("preset_mode"),
            date=data.get("date"),
        )

        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        area.add_schedule(schedule)
        await area_manager.async_save()

        return web.json_response({"success": True, "schedule": schedule.to_dict()})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_remove_schedule(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, schedule_id: str
) -> web.Response:
    """Remove schedule from an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        schedule_id: Schedule identifier

    Returns:
        JSON response
    """
    try:
        area_manager.remove_schedule_from_area(area_id, schedule_id)
        await area_manager.async_save()

        # Clear the schedule cache so the scheduler re-evaluates immediately
        schedule_executor = hass.data[DOMAIN].get("schedule_executor")
        if schedule_executor:
            schedule_executor.clear_schedule_cache(area_id)

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


async def handle_update_schedule(
    _hass: HomeAssistant,
    area_manager: AreaManager,
    area_id: str,
    schedule_id: str,
    data: dict,
) -> web.Response:
    """Update a schedule within an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        schedule_id: Schedule identifier
        data: Partial schedule fields to update

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        schedule = area.schedules.get(schedule_id)
        if not schedule:
            return web.json_response(
                {"error": f"Schedule {schedule_id} not found in area {area_id}"},
                status=404,
            )

        # Build base dict from existing schedule and overlay incoming fields
        existing = schedule.to_dict()
        # Allow both frontend 'days' (Monday etc) or short codes
        for k, v in data.items():
            existing[k] = v

        # If days was provided and is an empty list, treat that as a full deletion request
        if (
            "days" in data
            and isinstance(data.get("days"), list)
            and len(data.get("days")) == 0
        ):
            area.remove_schedule(schedule_id)
            await area_manager.async_save()
            return web.json_response({"success": True, "deleted": True})

        # If caller provided 'days', remove 'day' single-day field to avoid override
        if "days" in data and "day" in existing:
            existing.pop("day", None)
        # If caller provided 'day', remove 'days' list key to avoid ambiguity
        if "day" in data and "days" in existing:
            existing.pop("days", None)

        # Recreate schedule object from dict to normalize fields
        updated = Schedule.from_dict(existing)
        # Ensure id persists
        updated.schedule_id = schedule_id

        # Replace in area schedules
        area.schedules[schedule_id] = updated
        await area_manager.async_save()

        return web.json_response({"success": True, "schedule": updated.to_dict()})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_set_preset_mode(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set preset mode for an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with preset_mode

    Returns:
        JSON response
    """
    preset_mode = data.get("preset_mode")
    if not preset_mode:
        return web.json_response({"error": "preset_mode required"}, status=400)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        old_preset = area.preset_mode
        old_target = area.target_temperature
        old_effective = area.get_effective_target_temperature()

        _LOGGER.warning(
            "🎛️  API: SET PRESET MODE for %s: '%s' → '%s' | Current temp: %.1f°C, Effective: %.1f°C",
            area.name,
            old_preset,
            preset_mode,
            old_target,
            old_effective,
        )

        area.set_preset_mode(preset_mode)

        # Clear manual override mode when user sets preset via app
        if hasattr(area, "manual_override") and area.manual_override:
            _LOGGER.warning(
                "🔓 Clearing manual override for %s - preset mode now in control",
                area.name,
            )
            area.manual_override = False

        await area_manager.async_save()

        # Get new effective temperature
        new_effective = area.get_effective_target_temperature()

        _LOGGER.warning(
            "✓ Preset applied: %s → '%s' | Effective temp: %.1f°C → %.1f°C (base: %.1f°C)",
            area.name,
            preset_mode,
            old_effective,
            new_effective,
            old_target,
        )

        # Trigger immediate climate control to apply new temperature
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            await climate_controller.async_control_heating()
            _LOGGER.info("Triggered immediate climate control after preset change")

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True, "preset_mode": preset_mode})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_set_boost_mode(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set boost mode for an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with duration and optional temperature

    Returns:
        JSON response
    """
    duration = data.get("duration", 60)
    temp = data.get("temperature")

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.set_boost_mode(duration, temp)
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response(
            {
                "success": True,
                "boost_active": True,
                "duration": duration,
                "temperature": area.boost_temp,
            }
        )
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_cancel_boost(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Cancel boost mode for an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.cancel_boost_mode()
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True, "boost_active": False})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)
