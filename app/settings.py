from typing import List, Dict, Any
from pydantic import BaseModel, validator


class History(BaseModel):
    enabled: bool = False
    file: str = "history.txt"


class Agent(BaseModel):
    prompts: List[str]
    temperature: float = 0
    name: str = "Bobik"
    max_tries: int = 3
    sleep_seconds_between_tries: int = 2
    agent_type: str = "conversational-react-description"
    max_iterations: int = 4
    tools_enabled: bool = True


class Phrases(BaseModel):
    exit: List[str]
    with_tools: List[str]
    no_tools: List[str]
    run_once: List[str]
    clear_memory: List[str]
    quiet: List[str]
    verbose: List[str]


class PreParser(BaseModel):
    enabled: bool = True


class Tool(BaseModel):
    enabled: bool = False
    config_file: str = None


class User(BaseModel):
    location: str
    name: str = "Human"
    timezone: str = None


class ModelConfig(BaseModel):
    provider: str
    model: str
    endpoint_id: str = None
    agent_type: str = None
    temperature: float = None
    synonyms: List[str] = []
    tools_enabled: bool = None
    prompts: List[str] = None
    base_url: str = None


class IOInputConfig(BaseModel):
    provider: str
    model: str = None
    punctuate: bool = None
    language: str = None
    encoding: str = None
    channels: int = None
    sample_rate: int = None
    endpointing: int = None
    smart_format: bool = None


class IOOutputConfig(BaseModel):
    provider: str
    performance: str = None
    encoding: str = None
    sample_rate: int = None
    model: str = None


class PreParsers(BaseModel):
    clipboard: PreParser
    time: PreParser
    file: PreParser


class Tools(BaseModel):
    bing_search: Tool
    bing_news: Tool
    wttr_weather: Tool
    wikipedia: Tool
    google_search: Tool
    clear_memory: Tool
    date_time_tool: Tool
    input_switch: Tool
    available_models: Tool
    change_model: Tool
    end_conversation: Tool
    enable_disable_tools: Tool
    output_switch: Tool
    ics_calendar: Tool

    def get(self, name: str) -> Tool:
        return getattr(self, name)


class Settings(BaseModel):
    agent: Agent
    user: User
    phrases: Phrases
    models: Dict[str, ModelConfig]
    io_input: Dict[str, IOInputConfig]
    io_output: Dict[str, IOOutputConfig]
    prompts: Dict[str, Any]
    history: History = None
    pre_parsers: PreParsers = None
    tools: Tools = None
    tasks: Dict[str, List[str]] = []
