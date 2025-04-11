from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
import asyncio
import os


class MakeStorygenStory(BaseTool):
    name: str = "make_story"
    description: str = (
        "Writes a bedtime story and sends to user as audio file. "
        "Use this tool when asked to generate, make or read a bedtime story. "
        "Input is a prompt about what story should be about. "
        "Successful story generation will contain audio file name that user will access themselves."
    )

    def _run(self, prompt: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        print(f"Running {self.name} with prompt: {prompt}")

        cmd = ["storygen", "story", "create", prompt]

        env = {
            **os.environ,
            "HOME": os.path.expanduser("~"),
        }
        async def run_async_subprocess():
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await proc.communicate()
            return stdout, stderr, proc.returncode

        # Get the current event loop (works even if one is running)
        #stdout, stderr, returncode = asyncio.run(run_async_subprocess())
        loop = asyncio.get_event_loop()
        stdout, stderr, returncode = loop.run_until_complete(run_async_subprocess())

        output = stdout.decode()
        print(f"STDOUT: {output}")
        if stderr:
            print(f"STDERR: {stderr.decode()}")

        # get very last line from output
        output = output.strip().splitlines()[-1] # 2025/04/11 20:10:11 mp3: mp3/clean_final_groomed_The_Jungle_Heroes_Rise.mp3
        file = output.split(": ")[-1]

        return f"Story audio file created successfully in {file}"

    async def _arun(self, *args, **kwargs):
        """Use the tool asynchronously. Not implemented."""
        raise NotImplementedError
