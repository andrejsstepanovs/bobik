# Examples

Here are some examples of how you can customize the App using the `my_config.yaml` file:

Check configuration files in each example folder to see how you can customize the app.

## Setup
Place `.env` file in root folder of the project and set `BOBIK_CONFIG_FILE` value to point to `my_config.yaml` file.
It can actually point directly to example folder you want to use.

Then run app:
```
python computer.py
python ./run.py once
python ./run.py once quiet
python ./run.py once quiet tell me 2 software engineering jokes
echo "Hi" | python ./run.py once quiet
python ./run.py llm once code refactor this file /home/path/to/file.py answer only with python
```


### GROQ with DEEPGRAM voice `2_minimal_groq_with_voice`

This will enable text to speach and speach to text and you will be able to talk to the app.
```
BOBIK_CONFIG_FILE=MY_PATH_TO/docs/examples/2_minimal_groq_with_voice/my_config.yaml
GROQ_API_KEY=
DEEPGRAM_API_KEY=
```

Usage
```
python run.py vocal
python ./run.py once speak largest city in the world
python ./run.py once listen
python ./run.py
 > speak
 > how are you
```

! dont work in Windows

### Full

Full contains everything that is possible. You will need to examine config to understand what is possible and how it works. 

# TODO
Synonyms are not fully implemented. Use model name instead of synonyms.
