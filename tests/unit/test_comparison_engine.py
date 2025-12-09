"""Tests for comparison_engine module."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from smart_heating.comparison_engine import ComparisonEngine
from smart_heating.efficiency_calculator import EfficiencyCalculator


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
    return hass


@pytest.fixture
def mock_efficiency_calculator(mock_hass):
    """Create a mock EfficiencyCalculator."""
    calculator = Mock(spec=EfficiencyCalculator)
    calculator.calculate_area_efficiency = AsyncMock()
    return calculator


@pytest.fixture
def comparison_engine(mock_hass, mock_efficiency_calculator):
    """Create a ComparisonEngine instance."""
    return ComparisonEngine(mock_hass, mock_efficiency_calculator)


@pytest.mark.asyncio
async def test_comparison_engine_initialization(mock_hass, mock_efficiency_calculator):
    """Test ComparisonEngine initialization."""
    engine = ComparisonEngine(mock_hass, mock_efficiency_calculator)
    
    assert engine.hass == mock_hass
    assert engine.efficiency_calculator == mock_efficiency_calculator


@pytest.mark.asyncio
async def test_is_improvement_lower_is_better(comparison_engine):
    """Test is_improvement for metrics where lower is better."""
    # Heating time decreased (improvement)
    assert comparison_engine._is_improvement("heating_time_percentage", -5.0) is True
    
    # Heating time increased (not improvement)
    assert comparison_engine._is_improvement("heating_time_percentage", 5.0) is False
    
    # Temperature delta decreased (improvement)
    assert comparison_engine._is_improvement("average_temperature_delta", -1.0) is True
    
    # Cycles decreased (improvement)
    assert comparison_engine._is_improvement("heating_cycles", -2.0) is True


@pytest.mark.asyncio
async def test_is_improvement_higher_is_better(comparison_engine):
    """Test is_improvement for metrics where higher is better."""
    # Energy score increased (improvement)
    assert comparison_engine._is_improvement("energy_score", 5.0) is True
    
    # Energy score decreased (not improvement)
    assert comparison_engine._is_improvement("energy_score", -5.0) is False


@pytest.mark.asyncio
async def test_calculate_delta_basic(comparison_engine):
    """Test basic delta calculation."""
    period_a = {
        "heating_time_percentage": 60.0,
        "average_temperature_delta": 1.5,
        "heating_cycles": 10,
        "energy_score": 75.0,
        "temperature_stability": 0.5,
    }
    
    period_b = {
        "heating_time_percentage": 50.0,
        "average_temperature_delta": 1.0,
        "heating_cycles": 8,
        "energy_score": 80.0,
        "temperature_stability": 0.3,
    }
    
    delta = comparison_engine._calculate_delta(period_a, period_b)
    
    # Check heating time delta
    assert delta["heating_time_percentage"]["absolute"] == 10.0
    assert delta["heating_time_percentage"]["percentage"] == 20.0
    assert delta["heating_time_percentage"]["improved"] is False  # Increased
    
    # Check energy score delta
    assert delta["energy_score"]["absolute"] == -5.0
    assert delta["energy_score"]["percentage"] == -6.25
    assert delta["energy_score"]["improved"] is False  # Decreased


@pytest.mark.asyncio
async def test_calculate_delta_zero_division(comparison_engine):
    """Test delta calculation handles division by zero."""
    period_a = {"heating_time_percentage": 10.0}
    period_b = {"heating_time_percentage": 0.0}
    
    delta = comparison_engine._calculate_delta(period_a, period_b)
    
    # Should handle zero in period_b
    assert delta["heating_time_percentage"]["absolute"] == 10.0
    assert delta["heating_time_percentage"]["percentage"] == 100.0


@pytest.mark.asyncio
async def test_generate_comparison_summary_significant_improvement(comparison_engine):
    """Test summary generation for significant improvement."""
    delta = {
        "energy_score": {"percentage": 15.0},
        "heating_time_percentage": {"percentage": -10.0},
    }
    
    summary = comparison_engine._generate_comparison_summary(delta)
    
    assert "improved" in summary.lower()
    assert "15" in summary


@pytest.mark.asyncio
async def test_generate_comparison_summary_slight_improvement(comparison_engine):
    """Test summary generation for slight improvement."""
    delta = {
        "energy_score": {"percentage": 5.0},
        "heating_time_percentage": {"percentage": -2.0},
    }
    
    summary = comparison_engine._generate_comparison_summary(delta)
    
    assert "slightly improved" in summary.lower()


@pytest.mark.asyncio
async def test_generate_comparison_summary_decrease(comparison_engine):
    """Test summary generation for efficiency decrease."""
    delta = {
        "energy_score": {"percentage": -15.0},
        "heating_time_percentage": {"percentage": 10.0},
    }
    
    summary = comparison_engine._generate_comparison_summary(delta)
    
    assert "decreased" in summary.lower()


@pytest.mark.asyncio
async def test_energy_savings_description(comparison_engine):
    """Test energy savings description generation."""
    # Significant savings
    desc = comparison_engine._energy_savings_description(25.0)
    assert "significant" in desc.lower()
    
    # Moderate savings
    desc = comparison_engine._energy_savings_description(15.0)
    assert "moderate" in desc.lower()
    
    # Slight savings
    desc = comparison_engine._energy_savings_description(5.0)
    assert "slight" in desc.lower()
    
    # Slight increase
    desc = comparison_engine._energy_savings_description(-5.0)
    assert "slightly increased" in desc.lower()
    
    # Significant increase
    desc = comparison_engine._energy_savings_description(-15.0)
    assert "significantly increased" in desc.lower()


@pytest.mark.asyncio
async def test_compare_periods_day(comparison_engine, mock_efficiency_calculator):
    """Test comparing daily periods."""
    mock_efficiency_calculator.calculate_area_efficiency.side_effect = [
        {
            "heating_time_percentage": 60.0,
            "average_temperature_delta": 1.5,
            "heating_cycles": 10,
            "energy_score": 75.0,
            "temperature_stability": 0.5,
        },
        {
            "heating_time_percentage": 50.0,
            "average_temperature_delta": 1.0,
            "heating_cycles": 8,
            "energy_score": 80.0,
            "temperature_stability": 0.3,
        },
    ]
    
    result = await comparison_engine.compare_periods("living_room", "day", offset=1)
    
    assert result["area_id"] == "living_room"
    assert result["comparison_type"] == "day"
    assert "period_a" in result
    assert "period_b" in result
    assert "delta" in result
    assert "summary" in result


@pytest.mark.asyncio
async def test_compare_periods_week(comparison_engine, mock_efficiency_calculator):
    """Test comparing weekly periods."""
    mock_efficiency_calculator.calculate_area_efficiency.return_value = {
        "heating_time_percentage": 60.0,
        "energy_score": 75.0,
    }
    
    result = await comparison_engine.compare_periods("living_room", "week", offset=2)
    
    assert result["comparison_type"] == "week"
    assert "Last 2 week(s)" in result["period_b"]["name"]


@pytest.mark.asyncio
async def test_compare_periods_month(comparison_engine, mock_efficiency_calculator):
    """Test comparing monthly periods."""
    mock_efficiency_calculator.calculate_area_efficiency.return_value = {
        "heating_time_percentage": 60.0,
        "energy_score": 75.0,
    }
    
    result = await comparison_engine.compare_periods("living_room", "month", offset=1)
    
    assert result["comparison_type"] == "month"


@pytest.mark.asyncio
async def test_compare_periods_invalid_type(comparison_engine, mock_efficiency_calculator):
    """Test comparing with invalid period type raises error."""
    with pytest.raises(ValueError, match="Invalid comparison type"):
        await comparison_engine.compare_periods("living_room", "invalid", offset=1)


@pytest.mark.asyncio
async def test_compare_custom_periods(comparison_engine, mock_efficiency_calculator):
    """Test comparing custom time periods."""
    now = dt_util.now()
    start_a = now - timedelta(days=7)
    end_a = now
    start_b = now - timedelta(days=14)
    end_b = now - timedelta(days=7)
    
    mock_efficiency_calculator.calculate_area_efficiency.side_effect = [
        {"energy_score": 75.0, "heating_time_percentage": 60.0},
        {"energy_score": 70.0, "heating_time_percentage": 65.0},
    ]
    
    result = await comparison_engine.compare_custom_periods(
        "living_room", start_a, end_a, start_b, end_b
    )
    
    assert result["area_id"] == "living_room"
    assert result["comparison_type"] == "custom"
    assert result["period_a"]["name"] == "Period A"
    assert result["period_b"]["name"] == "Period B"


@pytest.mark.asyncio
async def test_compare_all_areas(comparison_engine, mock_efficiency_calculator):
    """Test comparing all areas."""
    mock_area_manager = Mock()
    mock_area_manager.get_area_ids.return_value = ["living_room", "bedroom"]
    mock_area_manager.get_area.side_effect = lambda area_id: {"enabled": True}
    
    mock_efficiency_calculator.calculate_area_efficiency.return_value = {
        "heating_time_percentage": 60.0,
        "average_temperature_delta": 1.0,
        "heating_cycles": 10,
        "energy_score": 75.0,
        "temperature_stability": 0.5,
    }
    
    results = await comparison_engine.compare_all_areas(
        mock_area_manager, "day", offset=1
    )
    
    assert len(results) == 2
    assert results[0]["area_id"] in ["living_room", "bedroom"]
    assert results[1]["area_id"] in ["living_room", "bedroom"]


@pytest.mark.asyncio
async def test_compare_all_areas_skips_disabled(comparison_engine, mock_efficiency_calculator):
    """Test that disabled areas are skipped in comparison."""
    mock_area_manager = Mock()
    mock_area_manager.get_area_ids.return_value = ["living_room", "bedroom"]
    mock_area_manager.get_area.side_effect = lambda area_id: {
        "enabled": area_id == "living_room"
    }
    
    mock_efficiency_calculator.calculate_area_efficiency.return_value = {
        "heating_time_percentage": 60.0,
        "energy_score": 75.0,
    }
    
    results = await comparison_engine.compare_all_areas(
        mock_area_manager, "day", offset=1
    )
    
    # Only living_room should be included
    assert len(results) == 1
    assert results[0]["area_id"] == "living_room"


@pytest.mark.asyncio
async def test_compare_all_areas_sorted_by_improvement(comparison_engine, mock_efficiency_calculator):
    """Test that results are sorted by energy score improvement."""
    mock_area_manager = Mock()
    mock_area_manager.get_area_ids.return_value = ["living_room", "bedroom"]
    mock_area_manager.get_area.side_effect = lambda area_id: {"enabled": True}
    
    # Mock different improvements for each area
    call_count = 0
    
    async def mock_calc(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count in [1, 2]:  # living_room (current, previous)
            return {
                "heating_time_percentage": 60.0,
                "energy_score": 85.0 if call_count == 1 else 75.0,  # +10% improvement
            }
        else:  # bedroom (current, previous)
            return {
                "heating_time_percentage": 60.0,
                "energy_score": 70.0 if call_count == 3 else 80.0,  # -10% improvement
            }
    
    mock_efficiency_calculator.calculate_area_efficiency.side_effect = mock_calc
    
    results = await comparison_engine.compare_all_areas(
        mock_area_manager, "day", offset=1
    )
    
    # Results should be sorted by improvement (best first)
    # living_room improved, bedroom decreased
    assert results[0]["area_id"] == "living_room"
    assert results[1]["area_id"] == "bedroom"
