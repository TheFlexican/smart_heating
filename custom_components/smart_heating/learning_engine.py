"""Adaptive learning engine for Smart Heating."""
import logging
from datetime import datetime, timedelta
from typing import Any
import statistics

from homeassistant.core import HomeAssistant
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    StatisticData,
    StatisticMetaData,
)
from homeassistant.const import UnitOfTemperature

_LOGGER = logging.getLogger(__name__)

# Minimum data points needed before making predictions
MIN_LEARNING_EVENTS = 20
MIN_LEARNING_DAYS = 7

# Statistic IDs for different metrics
STAT_HEATING_RATE = "smart_heating:heating_rate_{area_id}"
STAT_COOLDOWN_RATE = "smart_heating:cooldown_rate_{area_id}"
STAT_OUTDOOR_CORRELATION = "smart_heating:outdoor_correlation_{area_id}"
STAT_PREDICTION_ACCURACY = "smart_heating:prediction_accuracy_{area_id}"


class HeatingEvent:
    """Represents a single heating event for learning."""
    
    def __init__(
        self,
        area_id: str,
        start_time: datetime,
        end_time: datetime,
        start_temp: float,
        end_temp: float,
        outdoor_temp: float | None = None,
    ):
        """Initialize heating event.
        
        Args:
            area_id: Area identifier
            start_time: When heating started
            end_time: When heating ended
            start_temp: Temperature at start
            end_temp: Temperature at end
            outdoor_temp: Outdoor temperature during event
        """
        self.area_id = area_id
        self.start_time = start_time
        self.end_time = end_time
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.outdoor_temp = outdoor_temp
        
        # Calculate derived metrics
        self.duration_minutes = (end_time - start_time).total_seconds() / 60
        self.temp_change = end_temp - start_temp
        self.heating_rate = self.temp_change / self.duration_minutes if self.duration_minutes > 0 else 0


class LearningEngine:
    """Engine for learning heating patterns and making predictions."""
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the learning engine.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._active_heating_events: dict[str, dict[str, Any]] = {}
        self._weather_entity: str | None = None
        
        _LOGGER.debug("Learning engine initialized")
    
    async def async_setup(self) -> None:
        """Set up the learning engine."""
        # Auto-detect weather entity
        self._weather_entity = await self._async_detect_weather_entity()
        
        # Register statistics metadata for all metrics
        await self._async_register_statistics_metadata()
        
        _LOGGER.info("Learning engine setup complete (weather entity: %s)", self._weather_entity)
    
    async def _async_detect_weather_entity(self) -> str | None:
        """Auto-detect the weather entity.
        
        Returns:
            Weather entity ID or None if not found
        """
        # Look for weather entities
        for entity_id in self.hass.states.async_entity_ids("weather"):
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unknown", "unavailable"):
                _LOGGER.info("Auto-detected weather entity: %s", entity_id)
                return entity_id
        
        _LOGGER.warning("No weather entity found - outdoor temperature correlation disabled")
        return None
    
    async def _async_register_statistics_metadata(self) -> None:
        """Register metadata for statistics tracking."""
        # We'll register metadata when we first record data for each area
        # This is done dynamically per area
        pass
    
    def _get_statistic_id(self, metric_type: str, area_id: str) -> str:
        """Get statistic ID for a metric type and area.
        
        Args:
            metric_type: Type of metric (heating_rate, cooldown_rate, etc.)
            area_id: Area identifier
            
        Returns:
            Statistic ID string
        """
        return f"smart_heating:{metric_type}_{area_id}"
    
    async def _async_ensure_statistic_metadata(self, area_id: str, metric_type: str, name: str, unit: str) -> None:
        """Ensure statistic metadata is registered.
        
        Args:
            area_id: Area identifier
            metric_type: Type of metric
            name: Display name
            unit: Unit of measurement
        """
        statistic_id = self._get_statistic_id(metric_type, area_id)
        
        metadata = StatisticMetaData(
            has_mean=True,
            has_sum=False,
            name=name,
            source="smart_heating",
            statistic_id=statistic_id,
            unit_of_measurement=unit,
        )
        
        async_add_external_statistics(self.hass, metadata, [])
    
    async def async_start_heating_event(
        self,
        area_id: str,
        current_temp: float,
    ) -> None:
        """Record the start of a heating event.
        
        Args:
            area_id: Area identifier
            current_temp: Current temperature when heating started
        """
        outdoor_temp = await self._async_get_outdoor_temperature()
        
        self._active_heating_events[area_id] = {
            "start_time": datetime.now(),
            "start_temp": current_temp,
            "outdoor_temp": outdoor_temp,
        }
        
        _LOGGER.debug(
            "Started heating event for %s: temp=%.1f°C, outdoor=%.1f°C",
            area_id, current_temp, outdoor_temp or 0
        )
    
    async def async_end_heating_event(
        self,
        area_id: str,
        current_temp: float,
        target_reached: bool = True,
    ) -> None:
        """Record the end of a heating event and calculate learning metrics.
        
        Args:
            area_id: Area identifier
            current_temp: Current temperature when heating ended
            target_reached: Whether target temperature was reached
        """
        if area_id not in self._active_heating_events:
            _LOGGER.debug("No active heating event for %s to end", area_id)
            return
        
        event_data = self._active_heating_events.pop(area_id)
        
        event = HeatingEvent(
            area_id=area_id,
            start_time=event_data["start_time"],
            end_time=datetime.now(),
            start_temp=event_data["start_temp"],
            end_temp=current_temp,
            outdoor_temp=event_data.get("outdoor_temp"),
        )
        
        # Only record meaningful events (>5 minutes, >0.1°C change)
        if event.duration_minutes < 5 or abs(event.temp_change) < 0.1:
            _LOGGER.debug(
                "Skipping short/insignificant heating event for %s (%.1f min, %.2f°C)",
                area_id, event.duration_minutes, event.temp_change
            )
            return
        
        # Record to statistics
        await self._async_record_heating_event(event)
        
        _LOGGER.info(
            "Heating event recorded for %s: %.1f°C → %.1f°C in %.1f min (rate: %.3f°C/min, outdoor: %.1f°C)",
            area_id, event.start_temp, event.end_temp, event.duration_minutes,
            event.heating_rate, event.outdoor_temp or 0
        )
    
    async def _async_record_heating_event(self, event: HeatingEvent) -> None:
        """Record heating event to statistics database.
        
        Args:
            event: HeatingEvent instance
        """
        # Ensure metadata is registered
        await self._async_ensure_statistic_metadata(
            event.area_id, "heating_rate",
            f"Heating Rate - {event.area_id}", "°C/min"
        )
        
        # Record heating rate
        statistic_id = self._get_statistic_id("heating_rate", event.area_id)
        statistics_data = [
            StatisticData(
                start=event.start_time,
                mean=event.heating_rate,
                state=event.heating_rate,
            )
        ]
        
        metadata = StatisticMetaData(
            has_mean=True,
            has_sum=False,
            name=f"Heating Rate - {event.area_id}",
            source="smart_heating",
            statistic_id=statistic_id,
            unit_of_measurement="°C/min",
        )
        
        async_add_external_statistics(self.hass, metadata, statistics_data)
        
        # Record outdoor correlation if available
        if event.outdoor_temp is not None:
            await self._async_record_outdoor_correlation(event)
    
    async def _async_record_outdoor_correlation(self, event: HeatingEvent) -> None:
        """Record outdoor temperature correlation.
        
        Args:
            event: HeatingEvent instance
        """
        await self._async_ensure_statistic_metadata(
            event.area_id, "outdoor_correlation",
            f"Outdoor Temp - {event.area_id}", UnitOfTemperature.CELSIUS
        )
        
        statistic_id = self._get_statistic_id("outdoor_correlation", event.area_id)
        statistics_data = [
            StatisticData(
                start=event.start_time,
                mean=event.outdoor_temp,
                state=event.outdoor_temp,
            )
        ]
        
        metadata = StatisticMetaData(
            has_mean=True,
            has_sum=False,
            name=f"Outdoor Temp During Heating - {event.area_id}",
            source="smart_heating",
            statistic_id=statistic_id,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
        )
        
        async_add_external_statistics(self.hass, metadata, statistics_data)
    
    async def _async_get_outdoor_temperature(self) -> float | None:
        """Get current outdoor temperature from weather entity.
        
        Returns:
            Outdoor temperature or None if unavailable
        """
        if not self._weather_entity:
            return None
        
        state = self.hass.states.get(self._weather_entity)
        if not state:
            return None
        
        try:
            return float(state.attributes.get("temperature", 0))
        except (ValueError, TypeError):
            return None
    
    async def async_predict_heating_time(
        self,
        area_id: str,
        current_temp: float,
        target_temp: float,
    ) -> int | None:
        """Predict how many minutes needed to heat from current to target.
        
        Args:
            area_id: Area identifier
            current_temp: Current temperature
            target_temp: Target temperature
            
        Returns:
            Predicted minutes or None if insufficient data
        """
        # Get recent heating rate statistics
        heating_rates = await self._async_get_recent_heating_rates(area_id, days=30)
        
        if len(heating_rates) < MIN_LEARNING_EVENTS:
            _LOGGER.debug(
                "Insufficient data for prediction (need %d events, have %d)",
                MIN_LEARNING_EVENTS, len(heating_rates)
            )
            return None
        
        # Calculate average heating rate
        avg_rate = statistics.mean(heating_rates)
        
        # Adjust for outdoor temperature if available
        outdoor_temp = await self._async_get_outdoor_temperature()
        if outdoor_temp is not None:
            adjustment = await self._async_calculate_outdoor_adjustment(
                area_id, outdoor_temp
            )
            avg_rate *= adjustment
        
        # Calculate predicted time
        temp_change = target_temp - current_temp
        if temp_change <= 0 or avg_rate <= 0:
            return 0
        
        predicted_minutes = temp_change / avg_rate
        
        _LOGGER.debug(
            "Predicted heating time for %s: %.1f min (%.1f°C → %.1f°C at %.3f°C/min)",
            area_id, predicted_minutes, current_temp, target_temp, avg_rate
        )
        
        return int(predicted_minutes)
    
    async def _async_get_recent_heating_rates(
        self,
        area_id: str,
        days: int = 30
    ) -> list[float]:
        """Get recent heating rates from statistics.
        
        Args:
            area_id: Area identifier
            days: Number of days to look back
            
        Returns:
            List of heating rates
        """
        statistic_id = self._get_statistic_id("heating_rate", area_id)
        
        # Get statistics from recorder
        stats = await get_instance(self.hass).async_add_executor_job(
            get_last_statistics,
            self.hass,
            1,  # number of stats
            statistic_id,
            True,  # convert units
            {"mean"},  # types
        )
        
        if not stats or statistic_id not in stats:
            return []
        
        # Extract mean values
        rates = [s["mean"] for s in stats[statistic_id] if s.get("mean") is not None]
        return rates
    
    async def _async_calculate_outdoor_adjustment(
        self,
        area_id: str,
        current_outdoor_temp: float
    ) -> float:
        """Calculate heating rate adjustment based on outdoor temperature.
        
        Args:
            area_id: Area identifier
            current_outdoor_temp: Current outdoor temperature
            
        Returns:
            Adjustment factor (1.0 = no change, >1 = faster, <1 = slower)
        """
        # For now, simple linear adjustment
        # Colder outdoor = slower heating
        # This will be improved with actual correlation data later
        
        if current_outdoor_temp >= 15:
            return 1.1  # Slightly faster when warm outside
        elif current_outdoor_temp >= 5:
            return 1.0  # Normal
        elif current_outdoor_temp >= 0:
            return 0.9  # Slightly slower when cold
        else:
            return 0.8  # Slower when very cold
    
    async def async_calculate_smart_night_boost(
        self,
        area_id: str,
    ) -> float | None:
        """Calculate optimal night boost offset based on learning data.
        
        Args:
            area_id: Area identifier
            
        Returns:
            Recommended night boost offset or None if insufficient data
        """
        # Get cooldown rate during night hours
        # This would analyze how much the room cools overnight
        # For now, return None until we have enough data
        
        # TODO: Implement based on historical overnight cooldown patterns
        _LOGGER.debug("Smart night boost calculation not yet implemented for %s", area_id)
        return None
    
    async def async_get_learning_stats(self, area_id: str) -> dict[str, Any]:
        """Get learning statistics for an area.
        
        Args:
            area_id: Area identifier
            
        Returns:
            Dictionary with learning statistics
        """
        heating_rates = await self._async_get_recent_heating_rates(area_id, days=30)
        
        return {
            "data_points": len(heating_rates),
            "avg_heating_rate": statistics.mean(heating_rates) if heating_rates else 0,
            "min_heating_rate": min(heating_rates) if heating_rates else 0,
            "max_heating_rate": max(heating_rates) if heating_rates else 0,
            "ready_for_predictions": len(heating_rates) >= MIN_LEARNING_EVENTS,
            "outdoor_temp_available": self._weather_entity is not None,
        }
