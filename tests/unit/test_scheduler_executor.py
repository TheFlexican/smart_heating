from datetime import datetime, time
from types import SimpleNamespace
from unittest.mock import MagicMock

from smart_heating.scheduler import ScheduleExecutor


def make_hass():
    hass = MagicMock()
    hass.config = MagicMock()
    hass.config.time_zone = None
    return hass


def test_get_previous_day():
    hass = make_hass()
    se = ScheduleExecutor(hass, MagicMock())
    assert se._get_previous_day(0) == 6 or se._get_previous_day(0) == 6


def make_schedule(start, end, day, schedule_id="s1", preset_mode=None, temperature=None):
    return SimpleNamespace(
        start_time=start,
        end_time=end,
        day=day,
        schedule_id=schedule_id,
        preset_mode=preset_mode,
        temperature=temperature,
    )


def test_midnight_crossing_previous_day_match():
    hass = make_hass()
    sm = MagicMock()
    se = ScheduleExecutor(hass, sm)
    # schedule on Monday 22:00 - Tuesday 07:00
    sched_prev = make_schedule("22:00", "07:00", 0)
    # current day is Tuesday early morning 06:00
    cur_time = time.fromisoformat("06:00")
    active = se._find_active_schedule({"s1": sched_prev}, 1, cur_time)
    assert active == sched_prev


def test_midnight_crossing_today_match():
    hass = make_hass()
    se = ScheduleExecutor(hass, MagicMock())
    sched_today = make_schedule("22:00", "07:00", 1)
    cur_time = time.fromisoformat("23:00")
    active = se._find_active_schedule({"s1": sched_today}, 1, cur_time)
    assert active == sched_today


def test_normal_schedule_match():
    hass = make_hass()
    se = ScheduleExecutor(hass, MagicMock())
    sched = make_schedule("08:00", "17:00", 2)
    cur_time = time.fromisoformat("10:00")
    active = se._find_active_schedule({"s1": sched}, 2, cur_time)
    assert active == sched


def test_get_target_time_and_temp_from_schedule():
    hass = make_hass()
    am = MagicMock()
    se = ScheduleExecutor(hass, am)
    area = SimpleNamespace(area_id="a1", target_temperature=21.0)
    sched = make_schedule("07:15", "08:00", 3, temperature=20.5)
    now = datetime(2025, 12, 12, 6, 0)
    target_time, target_temp = se._get_target_time_and_temp_from_schedule(area, sched, now)
    assert target_time.hour == 7 and target_time.minute == 15
    assert abs(target_temp - 20.5) < 1e-6


def test_get_target_time_from_config_returns_none_and_value():
    hass = make_hass()
    se = ScheduleExecutor(hass, MagicMock())
    area = SimpleNamespace(area_id="a1", smart_night_boost_target_time=None)
    now = datetime(2025, 12, 12, 0, 0)
    assert se._get_target_time_from_config(area, now) is None
    area.smart_night_boost_target_time = "06:30"
    t = se._get_target_time_from_config(area, now)
    assert t.hour == 6 and t.minute == 30


def test_get_outdoor_temperature_various_units():
    hass = make_hass()
    se = ScheduleExecutor(hass, MagicMock())
    area = SimpleNamespace(area_id="a1", weather_entity_id=None)
    assert se._get_outdoor_temperature(area) is None

    area.weather_entity_id = "weather.home"
    state = MagicMock()
    state.state = "12.5"
    state.attributes = {"unit_of_measurement": "°C"}
    hass.states.get = MagicMock(return_value=state)
    temp = se._get_outdoor_temperature(area)
    assert abs(temp - 12.5) < 1e-6

    state.state = "55.0"
    state.attributes = {"unit_of_measurement": "°F"}
    hass.states.get = MagicMock(return_value=state)
    temp = se._get_outdoor_temperature(area)
    assert abs(temp - ((55.0 - 32) * 5 / 9)) < 1e-6

    state.state = "unavailable"
    hass.states.get = MagicMock(return_value=state)
    assert se._get_outdoor_temperature(area) is None
