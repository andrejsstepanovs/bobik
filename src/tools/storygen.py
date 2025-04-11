from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
import asyncio


class MakeStorygenStory(BaseTool):
    name: str = "make_story"
    description: str = (
        "Creates a bedtime story. "
        "Use this tool when asked to generate, make or read a bedtime story. "
        "Input is a prompt about what story should be about."
    )

    def _run(self, prompt: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        print(f"Running {self.name} with prompt: {prompt}")
        cmd = ["/usr/bin/storygen", "story", "create", prompt]

        async def run_async_subprocess():
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return stdout, stderr, proc.returncode

        # Get the current event loop (works even if one is running)
        loop = asyncio.get_event_loop()
        stdout, stderr, returncode = loop.run_until_complete(run_async_subprocess())

        output = stdout.decode()
        print(f"STDOUT: {output}")
        if stderr:
            print(f"STDERR: {stderr.decode()}")

        # get very last line from output
        output = output.decode("utf-8").strip().splitlines()[-1] # 2025/04/11 20:10:11 mp3: mp3/clean_final_groomed_The_Jungle_Heroes_Rise.mp3
        file = output.split(": ")[-1]

        return f"AI: Created storygen mp3 file {file}. You can tell the user to play the file. No need to do anything else. Thank you."
