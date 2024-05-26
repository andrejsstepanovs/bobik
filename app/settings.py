from typing import List, Dict, Any
from pydantic import BaseModel, validator

class History(BaseModel):
    enabled: bool
    file: str

class Agent(BaseModel):
    prompts: List[str]
    temperature: float
    name: str
    max_tries: int
    sleep_seconds_between_tries: int
    agent_type: str
    max_iterations: int
    tools_enabled: bool

class Phrases(BaseModel):
    exit: List[str]
    with_tools: List[str]
    no_tools: List[str]

class PreParser(BaseModel):
    enabled: bool

class Tool(BaseModel):
    enabled: bool
    config_file: str = None

class User(BaseModel):
    location: str
    name: str
    timezone: str = None

class ModelConfig(BaseModel):
    provider: str
    model: str
    agent_type: str = None
    temperature: float = None
    synonyms: List[str] = None
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
    model_switch: Tool
    end_conversation: Tool
    enable_disable_tools: Tool
    output_switch: Tool
    ics_calendar: Tool

    def get(self, name: str) -> Tool:
        return getattr(self, name)

class Settings(BaseModel):
    prompts: Dict[str, Any]
    history: History
    agent: Agent
    phrases: Phrases
    pre_parsers: PreParsers
    tools: Tools
    user: User
    models: Dict[str, ModelConfig]
    io_input: Dict[str, IOInputConfig]
    io_output: Dict[str, IOOutputConfig]
