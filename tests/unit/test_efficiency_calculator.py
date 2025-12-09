"""Tests for efficiency_calculator module."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from smart_heating.efficiency_calculator import EfficiencyCalculator


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
    return hass


@pytest.fixture
def mock_history_tracker():
    """Create a mock HistoryTracker instance."""
    tracker = MagicMock()
    tracker.get_history = MagicMock(return_value=[])
    return tracker


@pytest.fixture
def efficiency_calculator(mock_hass, mock_history_tracker):
    """Create an EfficiencyCalculator instance."""
    return EfficiencyCalculator(mock_hass, mock_history_tracker)


def create_history_entry(state_value, current_temp=20.0, target_temp=21.0, timestamp=None):
    """Create a history entry dict (as provided by HistoryTracker)."""
    return {
        "timestamp": (timestamp or dt_util.now()).isoformat(),
        "current_temperature": current_temp,
        "target_temperature": target_temp,
        "state": state_value,
    }


@pytest.mark.asyncio
async def test_calculate_heating_time_all_heating(efficiency_calculator):
    """Test heating time calculation when always heating."""
    history_data = [create_history_entry("heating") for _ in range(10)]
    
    result = efficiency_calculator._calculate_heating_time(history_data)
    
    assert result == 100.0


@pytest.mark.asyncio
async def test_calculate_heating_time_half_heating(efficiency_calculator):
    """Test heating time calculation when heating 50% of time."""
    history_data = (
        [create_history_entry("heating") for _ in range(5)] +
        [create_history_entry("idle") for _ in range(5)]
    )
    
    result = efficiency_calculator._calculate_heating_time(history_data)
    
    assert result == 50.0


@pytest.mark.asyncio
async def test_calculate_heating_time_no_states(efficiency_calculator):
    """Test heating time calculation with no states."""
    result = efficiency_calculator._calculate_heating_time([])
    assert result == 0.0


@pytest.mark.asyncio
async def test_calculate_avg_temp_delta(efficiency_calculator):
    """Test average temperature delta calculation."""
    history_data = [
        create_history_entry("heating", current_temp=19.0, target_temp=21.0),  # delta: 2.0
        create_history_entry("heating", current_temp=20.0, target_temp=21.0),  # delta: 1.0
        create_history_entry("idle", current_temp=21.0, target_temp=21.0),      # delta: 0.0
    ]
    
    result = efficiency_calculator._calculate_avg_temp_delta(history_data)
    
    # Average of absolute deltas: (2.0 + 1.0 + 0.0) / 3 = 1.0
    assert result == 1.0


@pytest.mark.asyncio
async def test_calculate_avg_temp_delta_no_states(efficiency_calculator):
    """Test avg temp delta with no states."""
    result = efficiency_calculator._calculate_avg_temp_delta([])
    assert result == 0.0


@pytest.mark.asyncio
async def test_count_heating_cycles(efficiency_calculator):
    """Test counting heating cycles."""
    history_data = [
        create_history_entry("idle"),
        create_history_entry("heating"),  # Cycle 1 start
        create_history_entry("heating"),
        create_history_entry("idle"),
        create_history_entry("heating"),  # Cycle 2 start
        create_history_entry("idle"),
        create_history_entry("heating"),  # Cycle 3 start
    ]
    
    result = efficiency_calculator._count_heating_cycles(history_data)
    
    assert result == 3


@pytest.mark.asyncio
async def test_count_heating_cycles_continuous_heating(efficiency_calculator):
    """Test counting cycles with continuous heating."""
    history_data = [create_history_entry("heating") for _ in range(10)]
    
    result = efficiency_calculator._count_heating_cycles(history_data)
    
    assert result == 0  # No cycles if always heating


@pytest.mark.asyncio
async def test_count_heating_cycles_no_states(efficiency_calculator):
    """Test counting cycles with no states."""
    result = efficiency_calculator._count_heating_cycles([])
    assert result == 0


@pytest.mark.asyncio
async def test_calculate_temp_stability(efficiency_calculator):
    """Test temperature stability calculation."""
    history_data = [
        create_history_entry("heating", current_temp=20.0),
        create_history_entry("heating", current_temp=20.0),
        create_history_entry("heating", current_temp=20.0),
    ]
    
    result = efficiency_calculator._calculate_temp_stability(history_data)
    
    # Std dev of [20, 20, 20] = 0
    assert result == 0.0


@pytest.mark.asyncio
async def test_calculate_temp_stability_variable_temps(efficiency_calculator):
    """Test temperature stability with variable temps."""
    history_data = [
        create_history_entry("heating", current_temp=18.0),
        create_history_entry("heating", current_temp=20.0),
        create_history_entry("heating", current_temp=22.0),
    ]
    
    result = efficiency_calculator._calculate_temp_stability(history_data)
    
    # Std dev should be > 0 for variable temps
    assert result > 0


@pytest.mark.asyncio
async def test_calculate_energy_score_perfect(efficiency_calculator):
    """Test energy score calculation for perfect conditions."""
    # Perfect: low heating time, small delta, few cycles
    score = efficiency_calculator._calculate_energy_score(
        heating_time_pct=30.0,
        avg_temp_delta=0.5,
        cycles=5,
        data_points=240,  # 2 hours of data
    )
    
    assert score == 100.0


@pytest.mark.asyncio
async def test_calculate_energy_score_high_heating_time(efficiency_calculator):
    """Test energy score penalty for high heating time."""
    # High heating time (80%)
    score = efficiency_calculator._calculate_energy_score(
        heating_time_pct=80.0,
        avg_temp_delta=0.5,
        cycles=5,
        data_points=240,
    )
    
    # Should be penalized: 100 - (80-50)*0.5 = 85
    assert score == 85.0


@pytest.mark.asyncio
async def test_calculate_energy_score_high_temp_delta(efficiency_calculator):
    """Test energy score penalty for high temperature delta."""
    # High temp delta (3°C)
    score = efficiency_calculator._calculate_energy_score(
        heating_time_pct=30.0,
        avg_temp_delta=3.0,
        cycles=5,
        data_points=240,
    )
    
    # Should be penalized: 100 - (3-1)*10 = 80
    assert score == 80.0


@pytest.mark.asyncio
async def test_calculate_energy_score_clamped_to_zero(efficiency_calculator):
    """Test energy score is clamped to 0."""
    # Terrible conditions
    score = efficiency_calculator._calculate_energy_score(
        heating_time_pct=90.0,
        avg_temp_delta=5.0,
        cycles=100,
        data_points=120,
    )
    
    assert score == 0.0


@pytest.mark.asyncio
async def test_generate_recommendations_good_efficiency(efficiency_calculator):
    """Test recommendations for good efficiency."""
    recommendations = efficiency_calculator._generate_recommendations(
        energy_score=85.0,
        heating_time_pct=40.0,
        avg_temp_delta=0.5,
        cycles=5,
    )
    
    assert len(recommendations) == 1
    assert "good" in recommendations[0].lower()


@pytest.mark.asyncio
async def test_generate_recommendations_low_efficiency(efficiency_calculator):
    """Test recommendations for low efficiency."""
    recommendations = efficiency_calculator._generate_recommendations(
        energy_score=40.0,
        heating_time_pct=40.0,
        avg_temp_delta=0.5,
        cycles=5,
    )
    
    assert len(recommendations) > 0
    assert any("low efficiency" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_high_heating_time(efficiency_calculator):
    """Test recommendations for high heating time."""
    recommendations = efficiency_calculator._generate_recommendations(
        energy_score=70.0,
        heating_time_pct=75.0,
        avg_temp_delta=0.5,
        cycles=5,
    )
    
    assert any("70%" in r for r in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_many_cycles(efficiency_calculator):
    """Test recommendations for many heating cycles."""
    recommendations = efficiency_calculator._generate_recommendations(
        energy_score=70.0,
        heating_time_pct=40.0,
        avg_temp_delta=0.5,
        cycles=25,
    )
    
    assert any("cycles" in r.lower() for r in recommendations)
    assert any("hysteresis" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_empty_metrics(efficiency_calculator):
    """Test empty metrics generation."""
    start = dt_util.now() - timedelta(days=1)
    end = dt_util.now()
    
    result = efficiency_calculator._empty_metrics("area1", "day", start, end)
    
    assert result["area_id"] == "area1"
    assert result["period"] == "day"
    assert result["heating_time_percentage"] == 0.0
    assert result["energy_score"] == 0.0
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_calculate_area_efficiency_integration(efficiency_calculator, mock_history_tracker):
    """Test full area efficiency calculation integration."""
    # Mock historical data
    history_data = [
        create_history_entry("heating", current_temp=19.5, target_temp=21.0),
        create_history_entry("heating", current_temp=20.0, target_temp=21.0),
        create_history_entry("idle", current_temp=21.0, target_temp=21.0),
    ] * 10  # Repeat to simulate more data
    
    mock_history_tracker.get_history.return_value = history_data
    
    result = await efficiency_calculator.calculate_area_efficiency(
        "living_room", period="day"
    )
    
    assert result["area_id"] == "living_room"
    assert result["period"] == "day"
    assert "heating_time_percentage" in result
    assert "energy_score" in result
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_calculate_area_efficiency_no_data(efficiency_calculator, mock_history_tracker):
    """Test efficiency calculation with no historical data."""
    mock_history_tracker.get_history.return_value = []
    
    result = await efficiency_calculator.calculate_area_efficiency(
        "living_room", period="day"
    )
    
    assert result["heating_time_percentage"] == 0.0
    assert result["data_points"] == 0
    assert "No data available" in result["recommendations"][0]


@pytest.mark.asyncio
async def test_calculate_all_areas_efficiency(efficiency_calculator, mock_history_tracker):
    """Test calculating efficiency for all areas."""
    mock_area_manager = Mock()
    mock_area_manager.get_all_areas.return_value = {
        "living_room": Mock(enabled=True),
        "bedroom": Mock(enabled=True),
    }
    
    history_data = [create_history_entry("heating")] * 10
    mock_history_tracker.get_history.return_value = history_data
    
    results = await efficiency_calculator.calculate_all_areas_efficiency(
        mock_area_manager, period="day"
    )
    
    assert len(results) == 2
    assert results[0]["area_id"] in ["living_room", "bedroom"]
    assert results[1]["area_id"] in ["living_room", "bedroom"]


@pytest.mark.asyncio
async def test_calculate_all_areas_skips_disabled(efficiency_calculator, mock_history_tracker):
    """Test that disabled areas are skipped."""
    mock_area_manager = Mock()
    mock_area_manager.get_all_areas.return_value = {
        "living_room": Mock(enabled=True),
        "bedroom": Mock(enabled=False),
    }
    
    history_data = [create_history_entry("heating")] * 10
    mock_history_tracker.get_history.return_value = history_data
    
    results = await efficiency_calculator.calculate_all_areas_efficiency(
        mock_area_manager, period="day"
    )
    
    # Only living_room should be included
    assert len(results) == 1
    assert results[0]["area_id"] == "living_room"
