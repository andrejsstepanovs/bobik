from typing import Optional, List
from datetime import datetime
import dateparser
import json
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from app.pkg.my_calendar import Calendar


class CalendarEventTool(BaseTool):
    """Tool for fetching calendar events."""

    name: str = "calendar_events"
    description: str = (
        "Use this tool to fetch upcoming calendar events. "
        "Tool has one optional argument that can have values like 'now', 'today', 'tomorrow' "
        "or specific date in format 'YYYY-MM-DD'."
        "Returns:"
        "A JSON string representing a weather."
    )

    calendar: Calendar = None

    def _run(
        self,
        date: Optional[str] = "Today",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        self.calendar.get_events()
        events = self.calendar.filter_and_sort_events()

        now: datetime = datetime.now()
        current_time: str = now.strftime("%Y-%m-%d %H:%M")
        output: List[str] = [f"Current time is {current_time}", "Here are calendar events:"]

        filter_date = dateparser.parse(date) if date else None

        for event in events:
            event_date = event["start"].strftime("%Y-%m-%d")
            if filter_date and filter_date.strftime("%Y-%m-%d") != event_date:
                continue

            output.append("")
            output.append(f"Date: {event_date} {'(Today)' if now.date() == event['start'].date() else ''}")
            output.append(f"Event: {event['summary'].replace(',', ' ')}")
            output.append(f"Time: {event['start'].strftime('%H:%M')} - {event['end'].strftime('%H:%M')}")
            output.append(f"Calendar: {event['calendar'] if event['calendar'].lower() != event['name'].lower() else event['name']}")

        return json.dumps(output)
