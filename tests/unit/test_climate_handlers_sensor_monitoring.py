"""Tests for climate_handlers/sensor_monitoring.py module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from homeassistant.const import STATE_ON, STATE_OFF

from smart_heating.climate_handlers.sensor_monitoring import SensorMonitoringHandler
from smart_heating.models.area import Area


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()
    manager.get_all_areas = MagicMock(return_value={})
    manager.global_presence_sensors = []
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_area_logger():
    """Create mock area logger."""
    logger = MagicMock()
    logger.log_event = MagicMock()
    return logger


@pytest.fixture
def sensor_handler(mock_hass, mock_area_manager, mock_area_logger):
    """Create SensorMonitoringHandler instance."""
    return SensorMonitoringHandler(mock_hass, mock_area_manager, mock_area_logger)


@pytest.fixture
def mock_area():
    """Create mock area."""
    area = MagicMock(spec=Area)
    area.area_id = "living_room"
    area.name = "Living Room"
    area.window_sensors = []
    area.window_is_open = False
    area.presence_sensors = []
    area.presence_detected = False
    area.use_global_presence = False
    area.auto_preset_enabled = False
    area.auto_preset_home = "home"
    area.auto_preset_away = "away"
    area.preset_mode = "home"
    return area


class TestSensorMonitoringHandlerInit:
    """Test SensorMonitoringHandler initialization."""

    def test_init_with_valid_params(self, mock_hass, mock_area_manager, mock_area_logger):
        """Test initialization with valid parameters."""
        handler = SensorMonitoringHandler(
            hass=mock_hass,
            area_manager=mock_area_manager,
            area_logger=mock_area_logger,
        )
        
        assert handler.hass == mock_hass
        assert handler.area_manager == mock_area_manager
        assert handler.area_logger == mock_area_logger


class TestCheckWindowSensors:
    """Test check_window_sensors method."""

    def test_check_window_sensors_no_sensors(self, sensor_handler, mock_area):
        """Test checking windows when no sensors configured."""
        mock_area.window_sensors = []
        
        result = sensor_handler.check_window_sensors("living_room", mock_area)
        
        assert result is False

    def test_check_window_sensors_all_closed(self, sensor_handler, mock_area, mock_hass):
        """Test checking windows when all are closed."""
        mock_area.window_sensors = [
            {"entity_id": "binary_sensor.window1"},
            {"entity_id": "binary_sensor.window2"},
        ]
        
        mock_state = MagicMock()
        mock_state.state = STATE_OFF
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        result = sensor_handler.check_window_sensors("living_room", mock_area)
        
        assert result is False
        assert mock_hass.states.get.call_count == 2

    def test_check_window_sensors_one_open(self, sensor_handler, mock_area, mock_hass):
        """Test checking windows when one is open."""
        mock_area.window_sensors = [
            {"entity_id": "binary_sensor.window1"},
            {"entity_id": "binary_sensor.window2"},
        ]
        
        def get_state(entity_id):
            mock_state = MagicMock()
            # First window open, second closed
            mock_state.state = STATE_ON if "window1" in entity_id else STATE_OFF
            return mock_state
        
        mock_hass.states.get = MagicMock(side_effect=get_state)
        
        result = sensor_handler.check_window_sensors("living_room", mock_area)
        
        assert result is True

    def test_check_window_sensors_all_open(self, sensor_handler, mock_area, mock_hass):
        """Test checking windows when all are open."""
        mock_area.window_sensors = [
            {"entity_id": "binary_sensor.window1"},
            {"entity_id": "binary_sensor.window2"},
        ]
        
        mock_state = MagicMock()
        mock_state.state = STATE_ON
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        result = sensor_handler.check_window_sensors("living_room", mock_area)
        
        assert result is True

    def test_check_window_sensors_unavailable_sensor(self, sensor_handler, mock_area, mock_hass):
        """Test checking windows when sensor is unavailable."""
        mock_area.window_sensors = [{"entity_id": "binary_sensor.window1"}]
        
        # Sensor returns None (unavailable)
        mock_hass.states.get = MagicMock(return_value=None)
        
        result = sensor_handler.check_window_sensors("living_room", mock_area)
        
        # Should treat as closed when unavailable
        assert result is False


class TestLogWindowStateChange:
    """Test log_window_state_change method."""

    def test_log_window_opened(self, sensor_handler, mock_area, mock_area_logger):
        """Test logging when window opens."""
        mock_area.window_is_open = False
        mock_area.name = "Living Room"
        
        sensor_handler.log_window_state_change("living_room", mock_area, True)
        
        # Should update area state
        assert mock_area.window_is_open is True
        
        # Should log event
        mock_area_logger.log_event.assert_called_once()
        call_args = mock_area_logger.log_event.call_args
        assert call_args[0][0] == "living_room"
        assert call_args[0][1] == "sensor"
        assert "opened" in call_args[0][2].lower()

    def test_log_window_closed(self, sensor_handler, mock_area, mock_area_logger):
        """Test logging when window closes."""
        mock_area.window_is_open = True
        mock_area.name = "Living Room"
        
        sensor_handler.log_window_state_change("living_room", mock_area, False)
        
        # Should update area state
        assert mock_area.window_is_open is False
        
        # Should log event
        mock_area_logger.log_event.assert_called_once()
        call_args = mock_area_logger.log_event.call_args
        assert call_args[0][0] == "living_room"
        assert call_args[0][1] == "sensor"
        assert "closed" in call_args[0][2].lower()

    def test_log_window_no_change(self, sensor_handler, mock_area, mock_area_logger):
        """Test logging when window state doesn't change."""
        mock_area.window_is_open = False
        
        sensor_handler.log_window_state_change("living_room", mock_area, False)
        
        # Should not log when no change
        mock_area_logger.log_event.assert_not_called()


class TestGetPresenceSensorsForArea:
    """Test get_presence_sensors_for_area method."""

    def test_get_area_specific_sensors(self, sensor_handler, mock_area):
        """Test getting area-specific presence sensors."""
        mock_area.use_global_presence = False
        mock_area.presence_sensors = [
            {"entity_id": "person.john"},
            {"entity_id": "binary_sensor.motion"},
        ]
        
        result = sensor_handler.get_presence_sensors_for_area(mock_area)
        
        assert result == mock_area.presence_sensors
        assert len(result) == 2

    def test_get_global_presence_sensors(self, sensor_handler, mock_area, mock_area_manager):
        """Test getting global presence sensors."""
        mock_area.use_global_presence = True
        mock_area_manager.global_presence_sensors = [
            {"entity_id": "person.jane"},
            {"entity_id": "person.bob"},
        ]
        
        result = sensor_handler.get_presence_sensors_for_area(mock_area)
        
        assert result == mock_area_manager.global_presence_sensors
        assert len(result) == 2

    def test_get_presence_sensors_empty_list(self, sensor_handler, mock_area):
        """Test getting presence sensors when none configured."""
        mock_area.use_global_presence = False
        mock_area.presence_sensors = []
        
        result = sensor_handler.get_presence_sensors_for_area(mock_area)
        
        assert result == []


class TestCheckPresenceSensors:
    """Test check_presence_sensors method."""

    def test_check_presence_no_sensors(self, sensor_handler):
        """Test checking presence when no sensors configured."""
        result = sensor_handler.check_presence_sensors("living_room", [])
        
        assert result is False

    def test_check_presence_person_home(self, sensor_handler, mock_hass):
        """Test checking presence when person is home."""
        sensors = [{"entity_id": "person.john"}]
        
        mock_state = MagicMock()
        mock_state.state = "home"
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        assert result is True

    def test_check_presence_person_away(self, sensor_handler, mock_hass):
        """Test checking presence when person is away."""
        sensors = [{"entity_id": "person.john"}]
        
        mock_state = MagicMock()
        mock_state.state = "not_home"
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        assert result is False

    def test_check_presence_motion_detected(self, sensor_handler, mock_hass):
        """Test checking presence when motion detected."""
        sensors = [{"entity_id": "binary_sensor.motion"}]
        
        mock_state = MagicMock()
        mock_state.state = STATE_ON
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        assert result is True

    def test_check_presence_motion_clear(self, sensor_handler, mock_hass):
        """Test checking presence when no motion."""
        sensors = [{"entity_id": "binary_sensor.motion"}]
        
        mock_state = MagicMock()
        mock_state.state = STATE_OFF
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        assert result is False

    def test_check_presence_multiple_sensors_all_away(self, sensor_handler, mock_hass):
        """Test checking presence with multiple sensors all away."""
        sensors = [
            {"entity_id": "person.john"},
            {"entity_id": "person.jane"},
            {"entity_id": "binary_sensor.motion"},
        ]
        
        mock_state = MagicMock()
        mock_state.state = "not_home"
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        assert result is False

    def test_check_presence_multiple_sensors_one_home(self, sensor_handler, mock_hass):
        """Test checking presence with multiple sensors, one home."""
        sensors = [
            {"entity_id": "person.john"},
            {"entity_id": "person.jane"},
        ]
        
        def get_state(entity_id):
            mock_state = MagicMock()
            # John away, Jane home
            mock_state.state = "home" if "jane" in entity_id else "not_home"
            return mock_state
        
        mock_hass.states.get = MagicMock(side_effect=get_state)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        assert result is True

    def test_check_presence_sensor_unavailable(self, sensor_handler, mock_hass):
        """Test checking presence when sensor is unavailable."""
        sensors = [{"entity_id": "person.john"}]
        
        # Sensor returns None (unavailable)
        mock_hass.states.get = MagicMock(return_value=None)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        # Should treat as no presence when unavailable
        assert result is False


class TestLogPresenceStateChange:
    """Test log_presence_state_change method."""

    def test_log_presence_detected(self, sensor_handler, mock_area_logger):
        """Test logging when presence is detected."""
        sensor_handler.log_presence_state_change("living_room", True)
        
        mock_area_logger.log_event.assert_called_once()
        call_args = mock_area_logger.log_event.call_args
        assert call_args[0][0] == "living_room"
        assert call_args[0][1] == "sensor"
        assert "detected" in call_args[0][2].lower()

    def test_log_presence_cleared(self, sensor_handler, mock_area_logger):
        """Test logging when presence is cleared."""
        sensor_handler.log_presence_state_change("living_room", False)
        
        mock_area_logger.log_event.assert_called_once()
        call_args = mock_area_logger.log_event.call_args
        assert call_args[0][0] == "living_room"
        assert call_args[0][1] == "sensor"
        assert "no presence" in call_args[0][2].lower()


class TestHandleAutoPresetChange:
    """Test handle_auto_preset_change method."""

    @pytest.mark.asyncio
    async def test_auto_preset_disabled(self, sensor_handler, mock_area, mock_area_manager):
        """Test auto preset when disabled."""
        mock_area.auto_preset_enabled = False
        
        await sensor_handler.handle_auto_preset_change("living_room", mock_area, True)
        
        # Should not change preset
        mock_area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_preset_change_to_home(self, sensor_handler, mock_area, mock_area_manager, mock_area_logger):
        """Test auto preset change to home when presence detected."""
        mock_area.auto_preset_enabled = True
        mock_area.auto_preset_home = "comfort"
        mock_area.auto_preset_away = "eco"
        mock_area.preset_mode = "eco"
        mock_area.name = "Living Room"
        
        await sensor_handler.handle_auto_preset_change("living_room", mock_area, True)
        
        # Should change to home preset
        assert mock_area.preset_mode == "comfort"
        mock_area_manager.async_save.assert_called_once()
        
        # Should log event
        mock_area_logger.log_event.assert_called_once()
        call_args = mock_area_logger.log_event.call_args
        assert "comfort" in call_args[0][2].lower()

    @pytest.mark.asyncio
    async def test_auto_preset_change_to_away(self, sensor_handler, mock_area, mock_area_manager, mock_area_logger):
        """Test auto preset change to away when no presence."""
        mock_area.auto_preset_enabled = True
        mock_area.auto_preset_home = "comfort"
        mock_area.auto_preset_away = "eco"
        mock_area.preset_mode = "comfort"
        mock_area.name = "Living Room"
        
        await sensor_handler.handle_auto_preset_change("living_room", mock_area, False)
        
        # Should change to away preset
        assert mock_area.preset_mode == "eco"
        mock_area_manager.async_save.assert_called_once()
        
        # Should log event
        mock_area_logger.log_event.assert_called_once()
        call_args = mock_area_logger.log_event.call_args
        assert "eco" in call_args[0][2].lower()

    @pytest.mark.asyncio
    async def test_auto_preset_no_change_needed(self, sensor_handler, mock_area, mock_area_manager):
        """Test auto preset when no change needed."""
        mock_area.auto_preset_enabled = True
        mock_area.auto_preset_home = "comfort"
        mock_area.auto_preset_away = "eco"
        mock_area.preset_mode = "comfort"  # Already correct
        
        await sensor_handler.handle_auto_preset_change("living_room", mock_area, True)
        
        # Should not save or change anything
        mock_area_manager.async_save.assert_not_called()


class TestAsyncUpdateSensorStates:
    """Test async_update_sensor_states method."""

    @pytest.mark.asyncio
    async def test_update_sensors_no_areas(self, sensor_handler, mock_area_manager):
        """Test updating sensors when no areas exist."""
        mock_area_manager.get_all_areas.return_value = {}
        
        # Should not raise exception
        await sensor_handler.async_update_sensor_states()

    @pytest.mark.asyncio
    async def test_update_sensors_checks_windows(self, sensor_handler, mock_area_manager, mock_area, mock_hass):
        """Test updating sensors checks window sensors."""
        mock_area_manager.get_all_areas.return_value = {"living_room": mock_area}
        mock_area.window_sensors = [{"entity_id": "binary_sensor.window1"}]
        
        mock_state = MagicMock()
        mock_state.state = STATE_ON
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        await sensor_handler.async_update_sensor_states()
        
        # Should update window state
        assert mock_area.window_is_open is True

    @pytest.mark.asyncio
    async def test_update_sensors_checks_presence(self, sensor_handler, mock_area_manager, mock_area, mock_hass):
        """Test updating sensors checks presence sensors."""
        mock_area_manager.get_all_areas.return_value = {"living_room": mock_area}
        mock_area.presence_sensors = [{"entity_id": "person.john"}]
        mock_area.use_global_presence = False
        
        mock_state = MagicMock()
        mock_state.state = "home"
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        await sensor_handler.async_update_sensor_states()
        
        # Should update presence state
        assert mock_area.presence_detected is True

    @pytest.mark.asyncio
    async def test_update_sensors_triggers_auto_preset(self, sensor_handler, mock_area_manager, mock_area, mock_hass):
        """Test updating sensors triggers auto preset change."""
        mock_area_manager.get_all_areas.return_value = {"living_room": mock_area}
        mock_area.presence_sensors = [{"entity_id": "person.john"}]
        mock_area.use_global_presence = False
        mock_area.auto_preset_enabled = True
        mock_area.auto_preset_home = "comfort"
        mock_area.auto_preset_away = "eco"
        mock_area.preset_mode = "eco"
        
        mock_state = MagicMock()
        mock_state.state = "home"
        mock_hass.states.get = MagicMock(return_value=mock_state)
        
        await sensor_handler.async_update_sensor_states()
        
        # Should change preset to comfort
        assert mock_area.preset_mode == "comfort"
        mock_area_manager.async_save.assert_called()

    @pytest.mark.asyncio
    async def test_update_sensors_multiple_areas(self, sensor_handler, mock_area_manager, mock_hass):
        """Test updating sensors for multiple areas."""
        area1 = MagicMock(spec=Area)
        area1.area_id = "living_room"
        area1.window_sensors = [{"entity_id": "binary_sensor.window1"}]
        area1.presence_sensors = []
        area1.use_global_presence = False
        area1.auto_preset_enabled = False
        area1.window_is_open = False
        area1.presence_detected = False
        
        area2 = MagicMock(spec=Area)
        area2.area_id = "bedroom"
        area2.window_sensors = [{"entity_id": "binary_sensor.window2"}]
        area2.presence_sensors = []
        area2.use_global_presence = False
        area2.auto_preset_enabled = False
        area2.window_is_open = False
        area2.presence_detected = False
        
        mock_area_manager.get_all_areas.return_value = {
            "living_room": area1,
            "bedroom": area2,
        }
        
        def get_state(entity_id):
            mock_state = MagicMock()
            # Window1 open, window2 closed
            mock_state.state = STATE_ON if "window1" in entity_id else STATE_OFF
            return mock_state
        
        mock_hass.states.get = MagicMock(side_effect=get_state)
        
        await sensor_handler.async_update_sensor_states()
        
        # Area1 window should be open, area2 closed
        assert area1.window_is_open is True
        assert area2.window_is_open is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_check_window_sensors_empty_entity_id(self, sensor_handler, mock_area, mock_hass):
        """Test checking window with malformed sensor config."""
        mock_area.window_sensors = [{"entity_id": ""}]
        
        mock_hass.states.get = MagicMock(return_value=None)
        
        result = sensor_handler.check_window_sensors("living_room", mock_area)
        
        # Should handle gracefully
        assert result is False

    def test_check_presence_mixed_sensor_types(self, sensor_handler, mock_hass):
        """Test checking presence with mix of person and motion sensors."""
        sensors = [
            {"entity_id": "person.john"},
            {"entity_id": "binary_sensor.motion1"},
            {"entity_id": "binary_sensor.motion2"},
        ]
        
        def get_state(entity_id):
            mock_state = MagicMock()
            if "person" in entity_id:
                mock_state.state = "not_home"
            elif "motion1" in entity_id:
                mock_state.state = STATE_ON  # Motion detected
            else:
                mock_state.state = STATE_OFF
            return mock_state
        
        mock_hass.states.get = MagicMock(side_effect=get_state)
        
        result = sensor_handler.check_presence_sensors("living_room", sensors)
        
        # Should return True because motion1 is on
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_auto_preset_with_custom_presets(self, sensor_handler, mock_area, mock_area_manager):
        """Test auto preset with custom preset names."""
        mock_area.auto_preset_enabled = True
        mock_area.auto_preset_home = "custom_home"
        mock_area.auto_preset_away = "custom_away"
        mock_area.preset_mode = "custom_away"
        
        await sensor_handler.handle_auto_preset_change("living_room", mock_area, True)
        
        # Should change to custom home preset
        assert mock_area.preset_mode == "custom_home"
