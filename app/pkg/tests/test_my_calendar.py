import pytest
import pytz
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.pkg.my_calendar import Calendar


# Sample data for testing
sample_state = MagicMock()
sample_options = {
    "ics": [
        {
            "type": "url",
            "url": "http://example.com/sample.ics",
            "name": "Sample Calendar",
            "calendar_name": "Sample",
            "private": False,
            "origin": "Sample Origin",
            "ics": ""
        }
    ],
    "cache": {
        "enabled": "No",
        "file": ""
    },
    "days": 7,
    "filter_status": [],
    "ignore_event_names": [],
    "emails": []
}

@pytest.fixture
def calendar():
    return Calendar(sample_state, sample_options)

def test_load_ics_files(calendar):
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = "Sample ICS data"
        calendar.load_ics_files()
        assert calendar.calendars["ics"][0]["ics"] == "Sample ICS data"

def test_load_calendar_events(calendar):
    calendar.calendars["ics"][0]["ics"] = "BEGIN:VCALENDAR\nEND:VCALENDAR"
    events = calendar.load_calendar_events()
    assert len(events) == 0

def test_filter_and_sort_events(calendar):
    now = datetime.now(tz=pytz.UTC)
    calendar.events = [
        {
            "start": now,
            "end": now + timedelta(days=1),
            "summary": "Test Event",
            "description": "Test Description",
            "organizer": "",
            "attendees": [],
            "status": "CONFIRMED"
        }
    ]
    events = calendar.filter_and_sort_events()
    assert len(events) == 1

def test_get_events(calendar):
    with patch('app.pkg.my_calendar.Calendar.load_ics_files') as mock_load_ics_files:
        with patch('app.pkg.my_calendar.Calendar.load_calendar_events') as mock_load_calendar_events:
            mock_load_calendar_events.return_value = []
            events = calendar.get_events()
            mock_load_ics_files.assert_called_once()
            mock_load_calendar_events.assert_called_once()
            assert events == []
