from unittest.mock import AsyncMock, MagicMock

import pytest
from smart_heating.climate_handlers.protection import ProtectionHandler


def make_hass():
    hass = MagicMock()
    hass.data = {"smart_heating": {}}
    return hass


def test_apply_frost_and_vacation_protection():
    hass = make_hass()
    am = MagicMock()
    am.frost_protection_enabled = True
    am.frost_protection_temp = 7.0
    ph = ProtectionHandler(hass, am)

    # frost protection raises target
    res = ph.apply_frost_protection("a1", 5.0)
    assert res == 7.0  # NOSONAR

    # vacation frost protection overrides
    vm = MagicMock()
    vm.is_active.return_value = True
    vm.get_min_temperature.return_value = 10.0
    hass.data["smart_heating"]["vacation_manager"] = vm
    res2 = ph.apply_frost_protection("a1", 6.0)
    assert res2 == 10.0  # NOSONAR


@pytest.mark.asyncio
async def test_apply_vacation_mode_and_manual_override_and_disabled_area():
    hass = make_hass()
    am = MagicMock()
    ph = ProtectionHandler(hass, am)
    vm = MagicMock()
    vm.is_active.return_value = True
    vm.get_preset_mode.return_value = "away"
    hass.data["smart_heating"]["vacation_manager"] = vm

    area = MagicMock()
    area.preset_mode = "comfort"
    ph.apply_vacation_mode("a1", area)
    assert area.preset_mode == "away"

    # manual override handling
    device_handler = MagicMock()
    device_handler.is_any_thermostat_actively_heating.return_value = True
    device_handler.async_control_switches = AsyncMock()
    ph.area_logger = MagicMock()
    await ph.async_handle_manual_override("a1", area, device_handler)
    device_handler.async_control_switches.assert_awaited()

    # disabled area handling
    history_tracker = MagicMock()
    history_tracker.async_record_temperature = AsyncMock()
    device_handler.async_control_thermostats = AsyncMock()
    device_handler.async_control_switches = AsyncMock()
    device_handler.async_control_valves = AsyncMock()
    area.current_temperature = 20.0
    area.target_temperature = 21.0
    area.get_thermostats.return_value = []
    area.get_switches.return_value = []
    area.get_valves.return_value = []
    await ph.async_handle_disabled_area("a1", area, device_handler, history_tracker, True)
    history_tracker.async_record_temperature.assert_awaited()
