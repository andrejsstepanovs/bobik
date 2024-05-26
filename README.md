# Bobik - AI Assistant

This project wraps most of langchain features and agent functionality and abstracts them into configuration file.
As a user, you need to set up necessary api keys in .env file and define your models in my_config.yaml file.

After that you will be able to talk with different LLMs using langchain agent with same kept memory. You can also enable, disable tools in config yaml file and inject your own tools easily.

Features:
- custom models
-- custom prompts and configuration
- all configuration fed into code from config file
- text to voice
-- with hotkey (2 x Alt) to start talking
- voice to text
-- with hotkey (2 x Alt) to prematurely stop
- keeps memory even if switching between different models
- tools with langchain agent
- quick stage change using pre-parser (question not sent to LLM) or via tools (LLM uses tool):
-- model switching
-- input switching
-- output switching
-- agent/llm switching
-- enable / disable agent mode
-- reset memory
-- enable / disable tools
-- graceful exit
- forever conversation loop (default)
- run only once (--once)
- --quiet mode if you dont need any other output (useful for scripting tasks)
- clipboard - includes clipboard in question
- Custom tools
-- Weather (wttr.in)
-- Calendar (local ics file parser & url)
-- Langchain tools
--- bing search
--- bing news
--- google search
--- wikipedia
- piping stdin input as question
- pasting input from clipboard - Use following template "my question here: <paste>" 
- llm providers
-- openai
-- groq
-- mistral
-- google - not tested (not possible in my country)
-- ollama
-- lm studio
-- custom openai api
- question / answer history text file

As you see a lot of functionality is baked into this app. This allows many unortodox and imaginative ways of using it. It can be chat, it can be one shot action, it can be plugged into bash scripts.

## License

The AI Assistant is licensed under the MIT License.

## Installation

To install the AI Assistant, follow these steps:

0. For Windows install: `python -m pip install pyreadline`.
1. Install ffplay if you want to have audio output.
2. Clone the repository from GitHub.
3. Install the required packages using `pip install -r requirements.txt`.
4. See `examples` to set up necessary environment variables and config yaml file.
5. Run the `run.py` script to start the AI Assistant.

## Windows
Main functionality on Windows is working fine. 

Not supported:
- deepgram autdio _input_ dont work. https://github.com/deepgram/deepgram-python-sdk/pull/398

Important:
- When providing file paths in yaml config files make sure to put values in single quotes! Like so: `'C:\my_path\file.xyw'`

# Mac
To be tested.

## Configuration

The App behavior and capabilities can be customized through a configuration file `my_config.yaml`.

See `examples` folder for more info.


### Pre-Parser

#### State change
The App pre-parsers can be used to change the model, input or output method and more things with the first words in the message. Here are some examples:

- To change the model to `gpt-3.5-turbo`, you can use the following pre-parser command: `run.py gpt-3.5-turbo speak listen tell me a story`.
- To change the input and output method to `voice`, you can use the following pre-parser command: `run.py verbal`.
- To change only input: `run.py listen`. Remember to have same name here that is configured in `my_config.yaml` file under `io_input`, `io_output` and `models`.
- Or just use default method that mostly should be set up as `text`: `run.py When I will have time for a jogging session. Check my calendar events and weather so it is not raining and I have no meetings then.`.

Note: These pre-parser commands should be included at the beginning of the first message.

#### Question manipulation

If enabled (config file) pre-parser will
- append clipboard
- append current time

### Voice Input and Output Capabilities

The AI Assistant has voice input and output capabilities, allowing you to interact with it using your voice. You will be able to double tap `Alt` button twice to start talking and prematurely stop long output from AI using same hotkey shortcut.

### Extensability

App is built with extensability in mind. Almost anything should be possible to change in runtime.

#### Adding Tools

Once you have created your tool class, you can add it to the `app/tools` directory and register it with the `ToolLoader` class. The `ToolLoader` class is responsible for loading and managing the tools used by the AI Assistant.

Here is an example of how you can create a custom tool:

1. Create a new Python file.
```python
from langchain.tools import BaseTool
from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun
```
2. Create a new class that inherits from the `BaseTool` class and implement the `_run` method:
```python
class MotivationTool(BaseTool):
    def _run(self, city: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Tool that reminds how great I am."""
        name: str = "my_custom_tool"
        description: str = (
            "Useful for when you need to know how great I am. "
            "Use this tool when phrases like 'I forgot how cool I am', 'I need motivation' are used."
        )
        return "Never forget how amazing you are."
```
3. Register the custom tool with the `ToolLoader` class by adding the following line to the `app/tool_loader.py` file:
```python
app = App()
# ... see app.py for more details
app.load_config_and_state()
app.load_options()
app.load_state_change_parser()
app.load_manager()
app.tool_provider.add_tool(MotivationTool())
app.start(False, "I need something to cheer me up.")
```

It is good idea to create your own main python script. Then origin future updates will not destroy your code.

## Usage

### Using the Tool as Is

To use the AI Assistant as is, simply run the `app.py` script and start interacting with it through the command line interface.
It will run in the loop using default `agent` (depends on model configuration) mode with memory attached.

### Using the Tool as a Library

You can also use the AI Assistant as a library in your own Python projects.
To do this, you need to import the necessary classes and functions from the `app` package and
create an instance of the `App` or `ConversationManager` class.

The `ConversationManager` class is responsible for managing the conversation between the user and the AI Assistant.
It provides various methods for sending messages, handling events, and customizing the behavior of the AI Assistant.

### Examples of Extending the Code with Self-Made Tools

Here are some examples of how you can extend the code with your own tools:

- You can create a tool that uses the Google Maps API to provide directions to a specific location.
- You can create a tool that uses the Twitter API to post tweets on your behalf.
- You can create a tool that uses the Spotify API to control your music playback.

### Examples of How to Execute the Project

Here are some examples of how you can execute the project:

- Using the `--quiet` mode:
If you want to run the AI Assistant in quiet mode, you can use the `--quiet` flag when running the `app.py` script.
In quiet mode, the AI Assistant will not print any messages to the console, except for LLM final answer.
```bash
python app.py --quiet
```
- Using different models:
If you want to use a different language model than the one that is enabled by default, you can use the model name when running the `app.py`.
The question pre-parser will hard match first parameters with available configuration and will change application state.
After that application will realize that state was changed and will reload the configuration, model and agent.

- Switching models during usage:
During usage, you can change models and history will be kept. So you can ask a story from one model and then switch to another model and ask for summary.
This works only when `--once` parameter is not used.
```bash
app.py --quiet groq tell me 3 sentence story
> Here is a 3 sentence story: As the sun set over the Berlin skyline, a young artist named Lena sat on the banks of the Spree River, her paintbrush dancing across the canvas as she tried to capture the vibrant colors of the city. Meanwhile, a group of friends laughed and chatted as they strolled along the riverbank, enjoying the warm summer evening. In the distance, the sounds of a street performer's guitar drifted through the air, adding to the lively atmosphere of the city.
> Master: gpt4o
> Master: summarize the story in 1 sentence
> A young artist paints the vibrant Berlin skyline by the Spree River as friends enjoy a warm summer evening with street music in the background.
```

There are also built in tools that will understand that you want to change model from the message.
```bash
app.py groq      
phrase 'groq' detected.
Changed model to groq
Got 1 args: ['groq']
text → groq (llama3-70b-8192) → write
Master: switch to gpt3 model please
Loading LLM...
Model: groq, LLM: llama3-70b-8192, Provider: groq, Temp: 0

> Entering new AgentExecutor chain...
Thought: Do I need to use a tool? Yes
Action: switch_model
Action Input: gpt3
Observation: Changed to gpt3
Thought: Do I need to use a tool? No
AI: Model switched to gpt3. I'm ready to assist you. How can I help you today?

> Finished chain.
Bobik: Model switched to gpt3. I'm ready to assist you. How can I help you today?
text → gpt3 (gpt-3.5-turbo) → write
Master: |
```
Same thing is implemented for:
- input change
- output change
- exit
- reset history, i.e. start new conversation
- turn on/off tools (agent vs no agent)

### Using the `--once` parameter:
If you want to run the AI Assistant only once and then exit, you can use the `--once` flag when running the `app.py` script.
The `--once` flag should be followed by the message that you want to send to the AI Assistant.
```bash
python app.py --once "What's the weather like today?"
```
The `--once` parameter is useful when you want to use the AI Assistant to perform a specific task and then exit, without having to interact with it through the command line interface.
It is good idea to combine `--once` together with `--quiet` parameter. Then you will get only answer without any additional information.
```bash
cat my_code.py | ./app.py --once --quiet Reformat given python code > my_code_reformatted.py
```

It is good idea to prepare specific model for these kind of tasks and in those tools use specialized `prompt`
and maybe disable tools with `tools_enabled: false` as it will be much faster without using agent (no tools == no agent).

```yaml
models:
  code:
    provider: mistral
    model: open-mixtral-8x22b
    tools_enabled: false
    prompts:
      - code
```

## Future Development

The App is constantly being improved and updated as we are using it daily.
In the future, we plan to add support for more language models and tools.
Main focus for now is implementing local voice to text and text to voice solution.

### Known issues
- re-work requirenments.txt
- Windows voice input is not working
- When running with `tools_enabled: false` history is not working
- Synonyms not implemented completely
- State input, output, model Tools are not dynamic (not using config parameters)

## Missing features to add
- Local text to voice & voice to text functionality is missing
- pip installation
- Package app in poetry
- Loading animation

Contributions are welcomed, feel free to submit a pull request or open an issue if you have any ideas or suggestions.
