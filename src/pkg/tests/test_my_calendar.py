import pytest
import pytz
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.pkg.my_calendar import Calendar


# Sample data for testing
sample_state = MagicMock()
sample_options: dict[str, list | int | bool] = {
    "ics": [{"type": str, "url": str, "name": str, "calendar_name": str, "private": bool, "origin": str, "ics": str}],
    "cache": {"enabled": str, "file": str},
    "days": int,
    "filter_status": list[str],
    "ignore_event_names": list[str],
    "emails": list[str]
}

@pytest.fixture
def calendar() -> Calendar:
    return Calendar(sample_state, sample_options)


def test_load_ics_files(calendar: Calendar):
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = "Sample ICS data"
        calendar.load_ics_files()
        assert calendar.calendars["ics"][0]["ics"] == "Sample ICS data"


def test_load_calendar_events(calendar: Calendar):
    calendar.calendars["ics"][0]["ics"] = "BEGIN:VCALENDAR\nEND:VCALENDAR"
    events: list[dict[str, datetime | str | list]] = calendar.load_calendar_events()
    assert len(events) == 0


def test_filter_and_sort_events(calendar: Calendar):
    now: datetime = datetime.now(tz=pytz.UTC)
    calendar.events = [{"start": datetime, "end": datetime, "summary": str, "description": str, "organizer": str, "attendees": list[str], "status": str}]
    events: list[dict[str, datetime | str | list]] = calendar.filter_and_sort_events()
    assert len(events) == 1


def test_get_events(calendar: Calendar):
    with patch('src.pkg.my_calendar.Calendar.load_ics_files') as mock_load_ics_files:
        with patch('src.pkg.my_calendar.Calendar.load_calendar_events') as mock_load_calendar_events:
            mock_load_calendar_events.return_value = []
            events: list[dict[str, datetime | str | list]] = calendar.get_events()
            mock_load_ics_files.assert_called_once()
            mock_load_calendar_events.assert_called_once()
            assert events == []
