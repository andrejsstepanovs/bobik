from typing import Optional
from datetime import datetime
from csv import reader
import dateparser
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from app.pkg.my_calendar import Calendar


class CalendarEventTool(BaseTool):
    """Tool for fetching calendar events."""

    name: str = "calendar_events"
    description: str = (
        "Use this tool to fetch upcoming calendar events. "
        "Tool have one optional argument that can have values like 'now', 'today', 'tomorrow' or specific date in format 'YYYY-MM-DD'."
    )
    calendar: Calendar = None

    def _run(
        self,
        date: str = "Today",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        self.calendar.get_events()
        events = self.calendar.filter_and_sort_events()

        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M")
        output = [
            f"Current time is {current_time}",
            "Here are calendar events:",
        ]

        filter_date = None
        if date is not None and date != "":
            filter_date = dateparser.parse(date)
            if filter_date is not None:
                filter_date_date = filter_date.strftime("%Y-%m-%d")

        for event in events:
            event_date = event["start"].strftime("%Y-%m-%d")
            is_today = current_time[:10] == event_date
            if filter_date is not None and filter_date_date != event_date:
                continue

            output.append("")
            output.append("Date: " + event_date + (" (Today)" if is_today else ""))
            output.append("Event: " + event["summary"].replace(",", " "))
            output.append("Time: " + event["start"].strftime("%H:%M") + " - " + event["end"].strftime("%H:%M"))
            calendar_name = event["calendar"]
            if calendar_name.lower() != event["name"].lower():
                calendar_name = calendar_name + " - " + event["name"]
            output.append("Calendar: " + calendar_name)

        return "\n".join(output).replace("`", "'")
