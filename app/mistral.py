from typing import Any, Iterator, List, Optional, Type, Mapping, AsyncIterator
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.outputs.chat_generation import ChatGenerationChunk
from langchain_core.messages import (
    AIMessageChunk,
    HumanMessageChunk,
    BaseMessageChunk,
    FunctionMessageChunk,
    ChatMessageChunk,
    SystemMessageChunk,
    BaseMessage
)
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain_community.llms.openai import acompletion_with_retry


def convert_delta_to_message_chunk(
    delta_dict: Mapping[str, Any], default_class: Type[BaseMessageChunk]
) -> BaseMessageChunk:
    role = delta_dict.get("role")
    content = delta_dict.get("content") or ""
    additional_kwargs = {"function_call": dict(delta_dict["function_call"])} if delta_dict.get("function_call") else {}

    if role == "user" or default_class == HumanMessageChunk:
        return HumanMessageChunk(content=content)
    elif role == "assistant" or default_class == AIMessageChunk:
        return AIMessageChunk(content=content, additional_kwargs=additional_kwargs)
    elif role == "system" or default_class == SystemMessageChunk:
        return SystemMessageChunk(content=content)
    elif role == "function" or default_class == FunctionMessageChunk:
        return FunctionMessageChunk(content=content, name=delta_dict["name"])
    elif role or default_class == ChatMessageChunk:
        return ChatMessageChunk(content=content, role=role)
    else:
        return default_class(content=content)


class EnhancedChatMistralAI(ChatMistralAI):
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        message_dicts, params = self._create_message_dicts(messages, stop)
        params.update(kwargs, stream=True)

        default_chunk_class = AIMessageChunk
        for chunk in self.completion_with_retry(
            messages=message_dicts, run_manager=run_manager, **params
        ):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if not delta.content and hasattr(delta, "tool_calls") and getattr(delta, "tool_calls"):
                delta.content = ""
            elif not delta.content:
                continue
            chunk = convert_delta_to_message_chunk(delta, default_chunk_class)
            default_chunk_class = chunk.__class__
            if run_manager:
                run_manager.on_llm_new_token(token=chunk.content, chunk=chunk)
            yield ChatGenerationChunk(message=chunk)

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        message_dicts, params = self._create_message_dicts(messages, stop)
        params.update(kwargs, stream=True)

        default_chunk_class = AIMessageChunk
        async for chunk in await acompletion_with_retry(
            self, messages=message_dicts, run_manager=run_manager, **params
        ):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if not delta.content and hasattr(delta, "tool_calls") and getattr(delta, "tool_calls"):
                delta.content = ""
            elif not delta.content:
                continue
            chunk = convert_delta_to_message_chunk(delta, default_chunk_class)
            default_chunk_class = chunk.__class__
            if run_manager:
                await run_manager.on_llm_new_token(token=chunk.content, chunk=chunk)
            yield ChatGenerationChunk(message=chunk)
