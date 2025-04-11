from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
import subprocess


class MakeStorygenStory(BaseTool):
    name: str = "make_story"
    description: str = (
        "Creates a bedtime story. "
        "Use this tool when asked to generate, make or read a bedtime story. "
        "Input is a prompt about what story should be about."
    )

    def _run(self, prompt: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        print(f"Running {self.name} with prompt: {prompt}")
        
        output = subprocess.run(["storygen", "story", "create", prompt], check=True, capture_output=True).stdout

        # get very last line from output
        output = output.decode("utf-8").strip().splitlines()[-1] # 2025/04/11 20:10:11 mp3: mp3/clean_final_groomed_The_Jungle_Heroes_Rise.mp3
        file = output.split(": ")[-1]

        return f"AI: Created storygen mp3 file {file}. You can tell the user to play the file. No need to do anything else. Thank you."
