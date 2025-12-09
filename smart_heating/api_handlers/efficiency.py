"""Efficiency report API handlers."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..efficiency_calculator import EfficiencyCalculator

_LOGGER = logging.getLogger(__name__)


async def handle_get_efficiency_report(
    hass: HomeAssistant,
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
            # Wrap in expected format with metrics nested
            return web.json_response({
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
            })
        else:
            # All areas report
            area_reports_raw = await efficiency_calculator.calculate_all_areas_efficiency(
                area_manager, period
            )
            
            # Transform each area report to match frontend structure
            area_reports = []
            for raw_report in area_reports_raw:
                area_reports.append({
                    "area_id": raw_report.get("area_id"),
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
                })
            
            # Calculate summary metrics from all areas
            if area_reports_raw:
                total_energy_score = sum(r.get("energy_score", 0) for r in area_reports_raw)
                total_heating_time = sum(r.get("heating_time_percentage", 0) for r in area_reports_raw)
                total_cycles = sum(r.get("heating_cycles", 0) for r in area_reports_raw)
                total_temp_delta = sum(r.get("average_temperature_delta", 0) for r in area_reports_raw)
                count = len(area_reports_raw)
                
                summary_metrics = {
                    "energy_score": total_energy_score / count,
                    "heating_time_percentage": total_heating_time / count,
                    "heating_cycles": total_cycles,
                    "avg_temp_delta": total_temp_delta / count,
                }
                
                # Generate summary recommendations based on overall metrics
                recommendations = []
                if summary_metrics["energy_score"] < 60:
                    recommendations.append("Overall efficiency is low. Review individual areas for issues.")
                if summary_metrics["heating_time_percentage"] > 60:
                    recommendations.append("System heating time is high. Consider global temperature adjustments.")
                if not recommendations:
                    recommendations.append("Overall system efficiency is good.")
            else:
                summary_metrics = {
                    "energy_score": 0,
                    "heating_time_percentage": 0,
                    "heating_cycles": 0,
                    "avg_temp_delta": 0,
                }
                recommendations = ["No area data available."]
            
            return web.json_response({
                "period": period,
                "start_date": area_reports[0]["start_date"] if area_reports else "",
                "end_date": area_reports[0]["end_date"] if area_reports else "",
                "summary_metrics": summary_metrics,
                "area_reports": area_reports,
                "recommendations": recommendations,
            })

    except Exception as e:
        _LOGGER.error("Error getting efficiency report: %s", e, exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_get_area_efficiency_history(
    hass: HomeAssistant,
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
            if period_type == "day":
                period_end = end - timedelta(days=i)
                period_start = period_end - timedelta(days=1)
            elif period_type == "week":
                period_end = end - timedelta(weeks=i)
                period_start = period_end - timedelta(weeks=1)
            elif period_type == "month":
                period_end = end - timedelta(days=30 * i)
                period_start = period_end - timedelta(days=30)
            else:
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
