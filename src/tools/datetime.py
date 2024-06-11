import time
from typing import Optional
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun


class TimeTool(BaseTool):
    """Tool for current time."""

    name: str = "time"
    description: str = "Use this tool when you need to find current time."

    def _run(self, location: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return_value: str = "AI: "+time.strftime("%H:%M:%S")
        return return_value


class DateTool(BaseTool):
    """Tool that gets current date."""

    name: str = "current_date"
    description: str = "Use this tool when you need to find current date."

    def _run(self, location: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return_value: str = "AI: "+time.strftime("%Y-%m-%d")
        return return_value


class DateTimeTool(BaseTool):
    """Tool that gets current date and time."""

    name: str = "current_datetime"
    description: str = (
        "Use this tool when you need to find current date or time. "
        "Tool have 1 argument `timezone` and it is always responsing with datetime with format 'YYYY-MM-DD HH:MM:SS'."
    )

    def _run(self, timezone: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return_value: str = "AI: Current date and time is: " + time.strftime("%Y-%m-%d %H:%M:%S")
        return return_value


class TextTool(BaseTool):
    """Tool that shows text."""

    name: str = "text"
    description: str = (
        "Use this tool when you need to find current date or time. "
        "Tool have 1 argument `timezone` and it is always responsing with datetime with format 'YYYY-MM-DD HH:MM:SS'."
    )

    def _run(self, timezone: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        current_time: float = time.time()
        current_struct_time: time.struct_time = time.localtime(current_time)
        return_value: str = "AI: Current date and time is: " + time.strftime("%Y-%m-%d %H:%M:%S", current_struct_time)
        return return_value
