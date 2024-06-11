import pytest
from unittest.mock import Mock
from src.history import History
from src.config import Configuration
from src.state import ApplicationState
from src.llm_agent import LargeLanguageModelAgent
from src.parsers import StateTransitionParser
from src.io_input import UserInput
from langchain_core.chat_history import BaseMessage
from langchain.memory import ConversationBufferMemory
import os


@pytest.fixture
def mock_config():
    config = Mock(spec=Configuration)
    config.agent_name = "TestAgent"
    config.history_file = "test_history.txt"
    return config

@pytest.fixture
def mock_state():
    state = Mock(spec=ApplicationState)
    state.are_tools_enabled = True
    return state

@pytest.fixture
def mock_agent():
    agent = Mock(spec=LargeLanguageModelAgent)
    agent.memory = Mock()
    agent.memory.chat_memory = Mock()
    agent.memory.chat_memory.messages = []
    return agent

@pytest.fixture
def mock_user_input():
    user_input = Mock(spec=UserInput)
    user_input.get.return_value = "Test input"
    return user_input

@pytest.fixture
def mock_parser():
    parser = Mock(spec=StateTransitionParser)
    return parser

@pytest.fixture
def history(config: Configuration, state: ApplicationState, agent: LargeLanguageModelAgent, user_input: UserInput, parser: StateTransitionParser):
    return History(config, state, agent, user_input, parser)

def test_save():
    # Arrange
    memory = Mock(spec=ConversationBufferMemory)
    memory.chat_memory = Mock()
    memory.chat_memory.messages = []

    agent = Mock(spec=LargeLanguageModelAgent)
    agent.memory = memory

    state = Mock(spec=ApplicationState)
    state.are_tools_enabled = False

    user_input = Mock(spec=UserInput)
    user_input.get.return_value = "Test input"

    config = Mock(spec=Configuration)
    config.agent_name = "AI"
    config.history_file = "test_history.txt"

    history = History(config, state, agent, user_input, Mock(spec=StateTransitionParser))

    # Act
    history.save(who="AI", text="Test text", force=False)

    # Assert
    memory.save_context.assert_called_once()
    user_input.get.assert_called_once()

    with open(config.history_file, "r") as read_file:
        content = read_file.read()

    assert "Test text" in content

    os.remove(config.history_file)

def test_remove_history_duplicates():
    messages = [Mock(spec=BaseMessage), Mock(spec=BaseMessage)]
    messages[0].pretty_repr.return_value = "Test message"
    messages[1].pretty_repr.return_value = "Test message"
    unique_messages = History._remove_history_duplicates(messages)
    assert len(unique_messages) == int(1)

def test_format_text():
    long_text = " ".join(["This is a long text that should be formatted into multiple lines." for _ in range(100)])
    formatted_text = History.format_text(long_text)
    assert len(formatted_text.split("\n")) > 1
