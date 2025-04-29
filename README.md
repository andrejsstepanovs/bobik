# AI Assistant
Yet another AI assistant.

## Description
Extendable and fully configurable command line LLM Agent that works on Windows, Linux and Mac.

You will be able to talk with different LLMs using different input and output methods.
App state changes are main functionality of this app, and can be done on the go in runtime. 

For example, you can ask for a story from one model,
then switch output to voice, switch to different model and ask it for a story summary.

You can pre-configure different flavors of models for specific tasks and then use them with `--once` parameter.

You can also toggle built in tools using config file and inject your own tools easily.

## Setup
This app wraps around langchain library 
and moves all configuration to user via config files.

As a user, you need to set up necessary api keys and config file location in 
`.env` file and define your models, tools, providers, etc. in `my_config.yaml` file.

See `docs/examples` folder for more info.

### shortcut
You can create a shortcut function in your shell to run the app more easily.

```bash
# .zshrc
function bobik() {
  /path/to/run.py "$@"
}
```

## License

The AI Assistant is licensed under the MIT License.

## Installation

To install the AI Assistant, follow these steps:

0. For Windows install: `python -m pip install pyreadline`.
1. Install ffplay if you want to have audio output.
2. For Ubuntu install audio `sudo apt install portaudio19-dev`
3. You need python dev lib too `sudo apt-get install python3-dev`
4. Clone the repository from GitHub.
5. Install the required packages using `pip install -r requirements.txt`.
6. See `docs/examples` to set up necessary environment variables and config yaml file.
7. Run the `run.py` script to start the AI Assistant.

## Windows
Main functionality on Windows is working fine. 

Not supported:
- deepgram autdio _input_ dont work. https://github.com/deepgram/deepgram-python-sdk/pull/398

Important:
- When providing file paths in yaml config files make sure to put values in single quotes! Like so: `'C:\my_path\file.xyw'`

# Mac
To be tested.


### Pre-Parser

Question pre-parser is enhancing question and also is checking for other phrases like to improve question sent to LLM.

If enabled (config file) pre-parser will:
- append clipboard
- append current time

State change pre-parser examples:
- quit - to exit the app
- llm - switch to simple mode
- agent - switch to agent mode
- verbal - switch to voice input/output
- speak - switch to voice output
- listen - switch to voice input
- any pre-defined model name - switch to that model

Most of the phrases are possible to edit in config file.


#### Add your tools and use as library to build agents

Check out how run.py works. You can script your solution quite easily.

### Usage Examples

Here are some examples of how you can execute the project:

```bash
python app.py --help
```


## Features:
- custom model configuration
-- custom prompts and configuration
- all configuration fed into code from config file
- text to voice
-- with hotkey (2 x Alt) to start talking
- voice to text
-- with hotkey (2 x Alt) to prematurely stop
- keeps memory even if switching between different models
- tools with langchain agent
- quick stage change using pre-parser (question not sent to LLM) or via tools (LLM uses tool):
-- model switching - based on your model configuration
-- input switching - see configs `text` / `listen` or `verbal` / `text`
-- output switching - see configs `text` / `speak` or `verbal` / `text`
-- enable / disable agent mode `llm` / `agent`
-- enable / disable tools ^^^
-- reset memory / forget history - `forget`
-- graceful exit - `quit` `q` (see config)
- forever conversation loop (default)
- run only `once`
- `quiet` mode if you don't need any other output (useful for scripting tasks)
- `clipboard` - includes clipboard in question
- `file` - includes file in question
- Custom tools
-- Weather (wttr.in)
-- Calendar (local ics file parser & url)
-- Langchain tools
--- bing search
--- bing news
--- google search
--- wikipedia
- piping stdin input as question
- pasting input from `clipboard` - Use following template "my question here: <paste>" 
- llm providers
-- `openai`
-- `groq`
-- `mistral`
-- `google` - not tested (not possible in my country)
-- `ollama`
-- `runpod`
-- `lm_studio`
-- `openai_custom`
- question / answer history text file - disable / enable in config file
- tasks - place where you can define frequently used prompt questions and use them in conversations.

As you see a lot of functionality is baked into this app. This allows many unortodox and imaginative ways of using it. It can be chat, it can be one shot action, it can be plugged into bash scripts.


## Future Development
The App is constantly being improved and updated as we are using it daily.
In the future, we plan to add support for more language models and tools.
Main focus for now is implementing local voice to text and text to voice solution.

### Known issues
- re-work requirenments.txt
- Windows voice input is not working
- Synonyms not implemented completely

## Missing features to add
- Local text to voice & voice to text functionality is missing
- pip installation
- Package app
- Loading animation

Contributions are welcomed, feel free to submit a pull request or open an issue if you have any ideas or suggestions.
