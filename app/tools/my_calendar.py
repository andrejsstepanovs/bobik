from typing import Optional
from datetime import datetime
from csv import reader

from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from app.pkg.my_calendar import Calendar


class CalendarEventTool(BaseTool):
    """Tool for fetching calendar events."""

    name: str = "calendar_events"
    description: str = "Use this tool to fetch upcoming calendar events."
    calendar: Calendar = None

    def _run(
        self,
        days: str = "Today",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        self.calendar.get_events()
        events = self.calendar.filter_and_sort_events()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        output = [
            f"Current time is {current_time}",
            "Here are calendar events:",
        ]

        for event in events:
            is_today = current_time[:10] == event["start"].strftime("%Y-%m-%d")
            if days.lower() == "today" and not is_today:
                continue

            output.append("")
            output.append("Date: " + event["start"].strftime("%Y-%m-%d") + (" (Today)" if is_today else ""))
            output.append("Event: " + event["summary"].replace(",", " "))
            output.append("Time: " + event["start"].strftime("%H:%M") + " - " + event["end"].strftime("%H:%M"))
            calendar_name = event["calendar"]
            if calendar_name.lower() != event["name"].lower():
                calendar_name = calendar_name + " - " + event["name"]
            output.append("Calendar: " + calendar_name)

        return "\n".join(output).replace("`", "'")
