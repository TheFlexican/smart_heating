"""Efficiency report API handlers."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..efficiency_calculator import EfficiencyCalculator
from typing import Any, Tuple

_LOGGER = logging.getLogger(__name__)


def _build_single_area_response(area_metrics: dict[str, Any]) -> dict[str, Any]:
    """Build a properly formatted single area report response.

    This helps keep the main API handler concise and reduces cognitive complexity.
    """
    return {
        "area_id": area_metrics.get("area_id"),
        "period": area_metrics.get("period"),
        "start_date": area_metrics.get("start_time", ""),
        "end_date": area_metrics.get("end_time", ""),
        "metrics": {
            "energy_score": area_metrics.get("energy_score", 0),
            "heating_time_percentage": area_metrics.get("heating_time_percentage", 0),
            "heating_cycles": area_metrics.get("heating_cycles", 0),
            "avg_temp_delta": area_metrics.get("average_temperature_delta", 0),
        },
        "recommendations": area_metrics.get("recommendations", []),
    }


def _transform_raw_report(
    raw_report: dict[str, Any], area_manager: AreaManager
) -> dict[str, Any]:
    """Transform a raw report dictionary into the API response structure.

    This abstracts away repeated mapping logic and keeps the handler smaller.
    """
    area_id = raw_report.get("area_id")
    area = area_manager.get_area(area_id) if area_id else None
    raw_area_name = getattr(area, "name", None) if area else None
    area_name = raw_area_name if isinstance(raw_area_name, str) else area_id

    return {
        "area_id": area_id,
        "area_name": area_name,
        "period": raw_report.get("period"),
        "start_date": raw_report.get("start_time", ""),
        "end_date": raw_report.get("end_time", ""),
        "metrics": {
            "energy_score": raw_report.get("energy_score", 0),
            "heating_time_percentage": raw_report.get("heating_time_percentage", 0),
            "heating_cycles": raw_report.get("heating_cycles", 0),
            "avg_temp_delta": raw_report.get("average_temperature_delta", 0),
        },
        "recommendations": raw_report.get("recommendations", []),
    }


def _calculate_summary_metrics(
    area_reports_raw: list[dict[str, Any]],
) -> Tuple[dict[str, Any], list[str]]:
    """Given a list of raw area reports, calculate summary metrics and recommendations.

    Returning a tuple keeps the callsites concise and easy to read.
    """
    total_energy_score = sum(r.get("energy_score", 0) for r in area_reports_raw)
    total_heating_time = sum(
        r.get("heating_time_percentage", 0) for r in area_reports_raw
    )
    total_cycles = sum(r.get("heating_cycles", 0) for r in area_reports_raw)
    total_temp_delta = sum(
        r.get("average_temperature_delta", 0) for r in area_reports_raw
    )
    count = len(area_reports_raw)

    summary_metrics = {
        "energy_score": total_energy_score / count,
        "heating_time_percentage": total_heating_time / count,
        "heating_cycles": total_cycles,
        "avg_temp_delta": total_temp_delta / count,
    }

    recommendations: list[str] = []
    if summary_metrics["energy_score"] < 60:
        recommendations.append(
            "Overall efficiency is low. Review individual areas for issues."
        )
    if summary_metrics["heating_time_percentage"] > 60:
        recommendations.append(
            "System heating time is high. Consider global temperature adjustments."
        )
    if not recommendations:
        recommendations.append("Overall system efficiency is good.")

    return summary_metrics, recommendations


async def _handle_all_areas_report(
    area_manager: AreaManager, efficiency_calculator: EfficiencyCalculator, period: str
) -> dict[str, Any]:
    """Async helper to build the all-areas report payload."""
    area_reports_raw = await efficiency_calculator.calculate_all_areas_efficiency(
        area_manager, period
    )

    area_reports = [_transform_raw_report(r, area_manager) for r in area_reports_raw]

    if area_reports_raw:
        summary_metrics, recommendations = _calculate_summary_metrics(area_reports_raw)
    else:
        summary_metrics = {
            "energy_score": 0,
            "heating_time_percentage": 0,
            "heating_cycles": 0,
            "avg_temp_delta": 0,
        }
        recommendations = ["No area data available."]

    return {
        "period": period,
        "start_date": area_reports[0]["start_date"] if area_reports else "",
        "end_date": area_reports[0]["end_date"] if area_reports else "",
        "summary_metrics": summary_metrics,
        "area_reports": area_reports,
        "recommendations": recommendations,
    }


async def handle_get_efficiency_report(
    _hass: HomeAssistant,
    area_manager: AreaManager,
    efficiency_calculator: EfficiencyCalculator,
    request: web.Request,
) -> web.Response:
    """Get efficiency report for areas.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        efficiency_calculator: Efficiency calculator instance
        request: HTTP request

    Returns:
        JSON response with efficiency metrics
    """
    try:
        # Get query parameters
        period = request.query.get("period", "day")
        area_id = request.query.get("area_id")

        if area_id and area_id != "all":
            # Single area report
            area_metrics = await efficiency_calculator.calculate_area_efficiency(
                area_id, period
            )
            # Build response using helper
            return web.json_response(_build_single_area_response(area_metrics))
        else:
            # All areas report - delegate to helper to reduce complexity
            payload = await _handle_all_areas_report(
                area_manager, efficiency_calculator, period
            )
            return web.json_response(payload)

    except Exception as e:
        _LOGGER.error("Error getting efficiency report: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_area_efficiency_history(
    _hass: HomeAssistant,
    efficiency_calculator: EfficiencyCalculator,
    request: web.Request,
    area_id: str,
) -> web.Response:
    """Get efficiency history for a specific area over multiple periods.

    Args:
        hass: Home Assistant instance
        efficiency_calculator: Efficiency calculator instance
        request: HTTP request
        area_id: Area ID

    Returns:
        JSON response with historical efficiency data
    """
    try:
        # Get query parameters
        periods = int(request.query.get("periods", "7"))  # Default 7 days
        period_type = request.query.get("period_type", "day")

        history_data = []

        # Calculate efficiency for each period
        from datetime import timedelta
        from homeassistant.util import dt as dt_util

        end = dt_util.now()

        for i in range(periods):
            if period_type == "week":
                period_end = end - timedelta(weeks=i)
                period_start = period_end - timedelta(weeks=1)
            elif period_type == "month":
                period_end = end - timedelta(days=30 * i)
                period_start = period_end - timedelta(days=30)
            else:  # Default to "day" for any other period_type
                period_end = end - timedelta(days=i)
                period_start = period_end - timedelta(days=1)

            metrics = await efficiency_calculator.calculate_area_efficiency(
                area_id, period_type, period_start, period_end
            )
            history_data.append(metrics)

        # Reverse to show oldest first
        history_data.reverse()

        return web.json_response({"history": history_data})

    except Exception as e:
        _LOGGER.error(
            "Error getting efficiency history for %s: %s", area_id, e, exc_info=True
        )
        return web.json_response({"error": str(e)}, status=500)
