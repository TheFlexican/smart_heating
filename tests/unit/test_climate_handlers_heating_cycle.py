"""Tests for climate_handlers.heating_cycle module."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from smart_heating.climate_handlers.heating_cycle import HeatingCycleHandler
from smart_heating.models import Area


class MockHomeAssistant:
    """Mock Home Assistant instance."""
    
    def __init__(self):
        """Initialize mock."""
        self.data = {
            "smart_heating": {
                "history": MagicMock()
            }
        }
        self.states = MagicMock()


@pytest.fixture
def mock_hass():
    """Return mocked Home Assistant instance."""
    return MockHomeAssistant()


@pytest.fixture
def mock_area_manager():
    """Return mocked area manager."""
    manager = MagicMock()
    manager.get_all_areas = MagicMock(return_value={})
    return manager


@pytest.fixture
def mock_learning_engine():
    """Return mocked learning engine."""
    engine = MagicMock()
    engine.async_start_heating_event = AsyncMock()
    engine.async_end_heating_event = AsyncMock()
    return engine


@pytest.fixture
def mock_area_logger():
    """Return mocked area logger."""
    logger = MagicMock()
    logger.log_event = MagicMock()
    return logger


@pytest.fixture
def mock_temp_handler():
    """Return mocked temperature handler."""
    handler = MagicMock()
    handler.collect_area_temperatures = MagicMock(return_value=[])
    handler.async_get_outdoor_temperature = AsyncMock(return_value=None)
    return handler


@pytest.fixture
def mock_sensor_handler():
    """Return mocked sensor handler."""
    handler = MagicMock()
    handler.async_update_sensor_states = AsyncMock()
    return handler


@pytest.fixture
def mock_device_handler():
    """Return mocked device handler."""
    handler = MagicMock()
    handler.async_control_thermostats = AsyncMock()
    handler.async_control_switches = AsyncMock()
    handler.async_control_valves = AsyncMock()
    handler.is_any_thermostat_actively_heating = MagicMock(return_value=False)
    return handler


@pytest.fixture
def mock_area():
    """Return mocked area."""
    area = MagicMock(spec=Area)
    area.get_temperature_sensors = MagicMock(return_value=[])
    area.get_thermostats = MagicMock(return_value=[])
    area.boost_mode_active = False
    area.check_boost_expiry = MagicMock()
    area.current_temperature = 20.0
    area.target_temperature = 21.0
    area.state = "idle"
    return area


@pytest.fixture
def heating_cycle_handler(mock_hass, mock_area_manager, mock_learning_engine, mock_area_logger):
    """Return HeatingCycleHandler instance."""
    return HeatingCycleHandler(
        hass=mock_hass,
        area_manager=mock_area_manager,
        learning_engine=mock_learning_engine,
        area_logger=mock_area_logger
    )


class TestHeatingCycleHandlerInit:
    """Test HeatingCycleHandler initialization."""
    
    def test_init_with_all_params(self, mock_hass, mock_area_manager, mock_learning_engine, mock_area_logger):
        """Test initialization with all parameters."""
        handler = HeatingCycleHandler(
            hass=mock_hass,
            area_manager=mock_area_manager,
            learning_engine=mock_learning_engine,
            area_logger=mock_area_logger
        )
        
        assert handler.hass == mock_hass
        assert handler.area_manager == mock_area_manager
        assert handler.learning_engine == mock_learning_engine
        assert handler.area_logger == mock_area_logger
        assert handler._area_heating_events == {}
        assert handler._record_counter == 0
    
    def test_init_without_optional_params(self, mock_hass, mock_area_manager):
        """Test initialization without optional parameters."""
        handler = HeatingCycleHandler(
            hass=mock_hass,
            area_manager=mock_area_manager
        )
        
        assert handler.hass == mock_hass
        assert handler.area_manager == mock_area_manager
        assert handler.learning_engine is None
        assert handler.area_logger is None


class TestAsyncPrepareHeatingCycle:
    """Test async_prepare_heating_cycle method."""
    
    @pytest.mark.asyncio
    async def test_prepare_with_no_areas(self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler):
        """Test preparation when no areas exist."""
        heating_cycle_handler.area_manager.get_all_areas.return_value = {}
        
        should_record, history = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        
        assert should_record is False
        assert history is not None
        mock_sensor_handler.async_update_sensor_states.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_with_temperature_sensors(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler, mock_area
    ):
        """Test preparation with temperature sensors."""
        mock_area.get_temperature_sensors.return_value = ["sensor.temp1"]
        mock_area.get_thermostats.return_value = []
        mock_temp_handler.collect_area_temperatures.return_value = [20.5, 21.0, 20.2]
        
        heating_cycle_handler.area_manager.get_all_areas.return_value = {
            "living_room": mock_area
        }
        
        should_record, history = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        
        # Temperature should be averaged
        assert mock_area.current_temperature == 20.566666666666666  # avg of [20.5, 21.0, 20.2]
        assert should_record is False
        mock_sensor_handler.async_update_sensor_states.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_with_thermostats(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler, mock_area
    ):
        """Test preparation with thermostats."""
        mock_area.get_temperature_sensors.return_value = []
        mock_area.get_thermostats.return_value = ["climate.thermostat1"]
        mock_temp_handler.collect_area_temperatures.return_value = [19.5]
        
        heating_cycle_handler.area_manager.get_all_areas.return_value = {
            "bedroom": mock_area
        }
        
        should_record, history = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        
        assert mock_area.current_temperature == 19.5
        assert should_record is False
    
    @pytest.mark.asyncio
    async def test_prepare_skips_area_without_sensors_or_thermostats(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler, mock_area
    ):
        """Test preparation skips areas without sensors or thermostats."""
        mock_area.get_temperature_sensors.return_value = []
        mock_area.get_thermostats.return_value = []
        
        heating_cycle_handler.area_manager.get_all_areas.return_value = {
            "empty_area": mock_area
        }
        
        should_record, history = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        
        # Should not call collect_area_temperatures
        mock_temp_handler.collect_area_temperatures.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_prepare_skips_area_with_no_temperature_readings(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler, mock_area
    ):
        """Test preparation when temperature collection returns empty."""
        mock_area.get_temperature_sensors.return_value = ["sensor.broken"]
        mock_area.get_thermostats.return_value = []
        mock_temp_handler.collect_area_temperatures.return_value = []  # No temps available
        
        original_temp = mock_area.current_temperature
        heating_cycle_handler.area_manager.get_all_areas.return_value = {
            "problematic_area": mock_area
        }
        
        should_record, history = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        
        # Temperature should not be updated
        assert mock_area.current_temperature == original_temp
    
    @pytest.mark.asyncio
    async def test_prepare_checks_boost_expiry(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler, mock_area
    ):
        """Test that boost mode expiry is checked."""
        mock_area.boost_mode_active = True
        mock_area.get_temperature_sensors.return_value = []
        mock_area.get_thermostats.return_value = []
        
        heating_cycle_handler.area_manager.get_all_areas.return_value = {
            "boosted_area": mock_area
        }
        
        await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        
        mock_area.check_boost_expiry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_history_recording_every_10_cycles(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler
    ):
        """Test that history recording is enabled every 10 cycles."""
        # First cycle
        should_record, _ = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        assert should_record is False
        assert heating_cycle_handler._record_counter == 1
        
        # 9 more cycles (total = 10)
        for i in range(9):
            should_record, _ = await heating_cycle_handler.async_prepare_heating_cycle(
                mock_temp_handler, mock_sensor_handler
            )
        
        assert should_record is True  # 10th cycle should record
        assert heating_cycle_handler._record_counter == 10
        
        # 11th cycle
        should_record, _ = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        assert should_record is False
        assert heating_cycle_handler._record_counter == 11


class TestAsyncHandleHeatingRequired:
    """Test async_handle_heating_required method."""
    
    @pytest.mark.asyncio
    async def test_handle_heating_required_without_learning_engine(
        self, mock_hass, mock_area_manager, mock_area, mock_device_handler, mock_temp_handler
    ):
        """Test heating required without learning engine."""
        handler = HeatingCycleHandler(
            hass=mock_hass,
            area_manager=mock_area_manager,
            learning_engine=None,  # No learning engine
            area_logger=None
        )
        
        heating_areas, max_target = await handler.async_handle_heating_required(
            "living_room", mock_area, 19.0, 21.0, mock_device_handler, mock_temp_handler
        )
        
        assert len(heating_areas) == 1
        assert heating_areas[0] == mock_area
        assert max_target == 21.0
        assert mock_area.state == "heating"
        
        # Should control all devices
        mock_device_handler.async_control_thermostats.assert_called_once_with(mock_area, True, 21.0)
        mock_device_handler.async_control_switches.assert_called_once_with(mock_area, True)
        mock_device_handler.async_control_valves.assert_called_once_with(mock_area, True, 21.0)
    
    @pytest.mark.asyncio
    async def test_handle_heating_required_with_learning_engine_new_event(
        self, heating_cycle_handler, mock_area, mock_device_handler, mock_temp_handler
    ):
        """Test heating required with learning engine starting new event."""
        mock_temp_handler.async_get_outdoor_temperature.return_value = 5.0
        
        heating_areas, max_target = await heating_cycle_handler.async_handle_heating_required(
            "living_room", mock_area, 18.5, 21.5, mock_device_handler, mock_temp_handler
        )
        
        assert len(heating_areas) == 1
        assert max_target == 21.5
        assert mock_area.state == "heating"
        
        # Should start learning event
        heating_cycle_handler.learning_engine.async_start_heating_event.assert_called_once_with(
            area_id="living_room",
            current_temp=18.5
        )
        
        # Outdoor temp should be fetched
        mock_temp_handler.async_get_outdoor_temperature.assert_called_once_with(mock_area)
    
    @pytest.mark.asyncio
    async def test_handle_heating_required_with_learning_engine_existing_event(
        self, heating_cycle_handler, mock_area, mock_device_handler, mock_temp_handler
    ):
        """Test heating required when event already active."""
        # Simulate active heating event
        heating_cycle_handler._area_heating_events["living_room"] = True
        
        await heating_cycle_handler.async_handle_heating_required(
            "living_room", mock_area, 19.0, 22.0, mock_device_handler, mock_temp_handler
        )
        
        # Should NOT start new learning event
        heating_cycle_handler.learning_engine.async_start_heating_event.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_heating_required_with_outdoor_temp_none(
        self, heating_cycle_handler, mock_area, mock_device_handler, mock_temp_handler
    ):
        """Test heating required when outdoor temp is not available."""
        mock_temp_handler.async_get_outdoor_temperature.return_value = None
        
        await heating_cycle_handler.async_handle_heating_required(
            "bedroom", mock_area, 17.0, 20.0, mock_device_handler, mock_temp_handler
        )
        
        # Should still work, just log N/A for outdoor temp
        heating_cycle_handler.learning_engine.async_start_heating_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_heating_required_with_area_logger(
        self, heating_cycle_handler, mock_area, mock_device_handler, mock_temp_handler
    ):
        """Test heating required logs events when area_logger is available."""
        await heating_cycle_handler.async_handle_heating_required(
            "kitchen", mock_area, 18.0, 21.0, mock_device_handler, mock_temp_handler
        )
        
        # Should log event
        heating_cycle_handler.area_logger.log_event.assert_called_once()
        call_args = heating_cycle_handler.area_logger.log_event.call_args
        
        assert call_args[0][0] == "kitchen"
        assert call_args[0][1] == "heating"
        assert "21.0°C" in call_args[0][2]
        assert call_args[0][3]["current_temp"] == 18.0
        assert call_args[0][3]["target_temp"] == 21.0
        assert call_args[0][3]["state"] == "heating"


class TestAsyncHandleHeatingStop:
    """Test async_handle_heating_stop method."""
    
    @pytest.mark.asyncio
    async def test_handle_heating_stop_thermostat_still_heating(
        self, heating_cycle_handler, mock_area, mock_device_handler
    ):
        """Test stopping heating when thermostat is still actively heating."""
        mock_device_handler.is_any_thermostat_actively_heating.return_value = True
        
        await heating_cycle_handler.async_handle_heating_stop(
            "living_room", mock_area, 21.0, 21.0, mock_device_handler
        )
        
        # Should still turn off devices
        mock_device_handler.async_control_thermostats.assert_called_once_with(mock_area, False, 21.0)
        mock_device_handler.async_control_switches.assert_called_once_with(mock_area, False)
        mock_device_handler.async_control_valves.assert_called_once_with(mock_area, False, 21.0)
        
        assert mock_area.state == "idle"
        
        # Should log special message about waiting for idle
        heating_cycle_handler.area_logger.log_event.assert_called_once()
        call_args = heating_cycle_handler.area_logger.log_event.call_args
        assert "still heating" in call_args[0][2]
        assert call_args[0][3]["state"] == "idle_pending"
    
    @pytest.mark.asyncio
    async def test_handle_heating_stop_normal(
        self, heating_cycle_handler, mock_area, mock_device_handler
    ):
        """Test normal heating stop."""
        mock_device_handler.is_any_thermostat_actively_heating.return_value = False
        
        await heating_cycle_handler.async_handle_heating_stop(
            "bedroom", mock_area, 21.5, 21.0, mock_device_handler
        )
        
        assert mock_area.state == "idle"
        
        # Should control all devices
        mock_device_handler.async_control_thermostats.assert_called_once_with(mock_area, False, 21.0)
        mock_device_handler.async_control_switches.assert_called_once_with(mock_area, False)
        mock_device_handler.async_control_valves.assert_called_once_with(mock_area, False, 21.0)
        
        # Should log normal stop event
        heating_cycle_handler.area_logger.log_event.assert_called_once()
        call_args = heating_cycle_handler.area_logger.log_event.call_args
        assert "stopped" in call_args[0][2]
        assert call_args[0][3]["state"] == "idle"
    
    @pytest.mark.asyncio
    async def test_handle_heating_stop_with_learning_engine_active_event(
        self, heating_cycle_handler, mock_area, mock_device_handler
    ):
        """Test stopping heating ends active learning event."""
        # Simulate active heating event
        heating_cycle_handler._area_heating_events["kitchen"] = True
        
        await heating_cycle_handler.async_handle_heating_stop(
            "kitchen", mock_area, 22.0, 22.0, mock_device_handler
        )
        
        # Should end learning event
        heating_cycle_handler.learning_engine.async_end_heating_event.assert_called_once_with(
            area_id="kitchen",
            current_temp=22.0
        )
        
        # Event should be removed from tracking
        assert "kitchen" not in heating_cycle_handler._area_heating_events
    
    @pytest.mark.asyncio
    async def test_handle_heating_stop_with_learning_engine_no_active_event(
        self, heating_cycle_handler, mock_area, mock_device_handler
    ):
        """Test stopping heating when no active learning event."""
        # No active event
        assert "bathroom" not in heating_cycle_handler._area_heating_events
        
        await heating_cycle_handler.async_handle_heating_stop(
            "bathroom", mock_area, 21.0, 21.0, mock_device_handler
        )
        
        # Should NOT end learning event
        heating_cycle_handler.learning_engine.async_end_heating_event.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_heating_stop_without_learning_engine(
        self, mock_hass, mock_area_manager, mock_area, mock_device_handler
    ):
        """Test stopping heating without learning engine."""
        handler = HeatingCycleHandler(
            hass=mock_hass,
            area_manager=mock_area_manager,
            learning_engine=None,
            area_logger=None
        )
        
        await handler.async_handle_heating_stop(
            "office", mock_area, 20.5, 20.0, mock_device_handler
        )
        
        assert mock_area.state == "idle"
        mock_device_handler.async_control_thermostats.assert_called_once()
        mock_device_handler.async_control_switches.assert_called_once()
        mock_device_handler.async_control_valves.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_heating_stop_without_area_logger(
        self, mock_hass, mock_area_manager, mock_area, mock_device_handler
    ):
        """Test stopping heating without area logger."""
        handler = HeatingCycleHandler(
            hass=mock_hass,
            area_manager=mock_area_manager,
            learning_engine=None,
            area_logger=None
        )
        
        await handler.async_handle_heating_stop(
            "hallway", mock_area, 19.0, 19.0, mock_device_handler
        )
        
        # Should not crash without area_logger
        assert mock_area.state == "idle"


class TestHeatingCycleIntegration:
    """Integration tests for heating cycle workflows."""
    
    @pytest.mark.asyncio
    async def test_full_heating_cycle_with_all_features(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler,
        mock_device_handler, mock_area
    ):
        """Test complete heating cycle from prepare to stop."""
        # Setup area with sensors
        mock_area.get_temperature_sensors.return_value = ["sensor.temp1"]
        mock_area.get_thermostats.return_value = ["climate.thermo1"]
        mock_temp_handler.collect_area_temperatures.return_value = [18.0]
        mock_temp_handler.async_get_outdoor_temperature.return_value = 3.5
        
        heating_cycle_handler.area_manager.get_all_areas.return_value = {
            "living_room": mock_area
        }
        
        # 1. Prepare heating cycle
        should_record, history = await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        
        assert mock_area.current_temperature == 18.0
        assert should_record is False
        
        # 2. Start heating
        heating_areas, max_target = await heating_cycle_handler.async_handle_heating_required(
            "living_room", mock_area, 18.0, 21.0, mock_device_handler, mock_temp_handler
        )
        
        assert mock_area.state == "heating"
        assert "living_room" in heating_cycle_handler._area_heating_events
        
        # 3. Update temperature (simulating warming up)
        mock_temp_handler.collect_area_temperatures.return_value = [21.0]
        await heating_cycle_handler.async_prepare_heating_cycle(
            mock_temp_handler, mock_sensor_handler
        )
        assert mock_area.current_temperature == 21.0
        
        # 4. Stop heating
        await heating_cycle_handler.async_handle_heating_stop(
            "living_room", mock_area, 21.0, 21.0, mock_device_handler
        )
        
        assert mock_area.state == "idle"
        assert "living_room" not in heating_cycle_handler._area_heating_events
        
        # Verify learning engine was used
        heating_cycle_handler.learning_engine.async_start_heating_event.assert_called_once()
        heating_cycle_handler.learning_engine.async_end_heating_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_areas_heating_independently(
        self, heating_cycle_handler, mock_temp_handler, mock_sensor_handler,
        mock_device_handler
    ):
        """Test multiple areas can heat independently."""
        # Create two areas
        area1 = MagicMock(spec=Area)
        area1.get_temperature_sensors.return_value = ["sensor.area1"]
        area1.get_thermostats.return_value = []
        area1.boost_mode_active = False
        area1.state = "idle"
        
        area2 = MagicMock(spec=Area)
        area2.get_temperature_sensors.return_value = ["sensor.area2"]
        area2.get_thermostats.return_value = []
        area2.boost_mode_active = False
        area2.state = "idle"
        
        heating_cycle_handler.area_manager.get_all_areas.return_value = {
            "area1": area1,
            "area2": area2
        }
        
        # Area 1 needs heating
        mock_temp_handler.collect_area_temperatures.return_value = [18.0]
        await heating_cycle_handler.async_handle_heating_required(
            "area1", area1, 18.0, 21.0, mock_device_handler, mock_temp_handler
        )
        
        # Area 2 also needs heating
        mock_temp_handler.collect_area_temperatures.return_value = [17.0]
        await heating_cycle_handler.async_handle_heating_required(
            "area2", area2, 17.0, 20.0, mock_device_handler, mock_temp_handler
        )
        
        # Both should be tracked
        assert "area1" in heating_cycle_handler._area_heating_events
        assert "area2" in heating_cycle_handler._area_heating_events
        assert area1.state == "heating"
        assert area2.state == "heating"
        
        # Stop area1 only
        await heating_cycle_handler.async_handle_heating_stop(
            "area1", area1, 21.0, 21.0, mock_device_handler
        )
        
        assert "area1" not in heating_cycle_handler._area_heating_events
        assert "area2" in heating_cycle_handler._area_heating_events
        assert area1.state == "idle"
        assert area2.state == "heating"
