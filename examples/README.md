# Examples

Here are some examples of how you can customize the App using the `my_config.yaml` file:

- You can specify the language model to be used by the AI Assistant by setting the `llm_model` value under the `models` section.
- You can enable or disable specific tools by setting the `enabled` value to `true` or `false` under the `tools` section.
- You can customize the AI Assistant's prompts by editing the `prompts` section.
- First model, input and output in the list will be used as default one.


Use these examples as starting point configuration.


## Setup
Place `.env` file in root folder of your code or this project and set `COMPUTER_CONFIG_FILE` value to point to `my_config.yaml` file.
It can actually point directly to example folder you want to use.

### Check if works with `1_minimal_groq` setup:

```
COMPUTER_CONFIG_FILE=MY_PATH_TO\examples\1_minimal_groq\my_config.yaml
GROQ_API_KEY=
```

Then run app:
```
python computer.py
```

Try other ways how you can run
```
python .\computer.py --once
python .\computer.py --once --quiet
python .\computer.py --once --quiet tell me 2 software engineering jokes
```

L:\computer\examples\full\my_config.yaml

### GROQ with DEEPGRAM voice `2_minimal_groq_with_voice`

```
COMPUTER_CONFIG_FILE=MY_PATH_TO\examples\2_minimal_groq_with_voice\my_config.yaml
GROQ_API_KEY=
DEEPGRAM_API_KEY=
```

## Switch output to speak:
Then run app:
- `speak` will match `io_output: speak` provider and send to LLM (groq) text: `how are you`.
```
python .\computer.py speak how are you

# alternative:
python .\computer.py
> speak
> how are you
```

If all is OK you should hear voice output that you should be able to stop prematurely with double tapping Alt key.

# Switch input to Listen:
### Dont work in Windows (for now)

```
python .\computer.py listen
```
You will need to double tap Alt key, then there will be a beep that announces that you can start speaking.
Your voice will be translated to txt by deepgram provider and fed into LLM (groq) that will respond in text.

# Switch all to voice:

There is shortcut input & output switch implemented: `verbal`.
It will set input and output to voice.

```
python .\computer.py verbal

# or
python .\computer.py
> verbal
# to switch back to text:
> text
```

### Full

Full contains everything that is possible. You will need to examine config to understand what is possible and how it works. 
I tried to document it in main README.md file, but could be I missed some features.
