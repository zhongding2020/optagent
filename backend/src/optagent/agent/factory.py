from typing import Any
from collections.abc import Sequence
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None
from langchain_core.language_models import BaseChatModel
from langchain_core.tools.base import BaseTool
from collections.abc import Callable

from ..config import AppConfig


def _resolve_model(config: AppConfig, tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None) -> BaseChatModel:
    provider = config.llm.provider
    model = config.llm.model
    # Bind tools if provided, so the model can call them
    if provider == "deepseek":
        import os
        return ChatOpenAI(
            model=model,
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
    elif provider == "openai":
        return ChatOpenAI(model=model)
    elif provider == "anthropic":
        return ChatAnthropic(model=model)
    elif provider == "ollama":
        if ChatOllama: return ChatOllama(model=model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def create_optagent_agent(
    config: AppConfig,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
) -> Any:
    """Create a deepagents agent with skills hot-plug support.

    Uses deepagents' built-in skills parameter which automatically
    configures SkillsMiddleware for progressive disclosure.
    """
    model = _resolve_model(config)
    agent = create_deep_agent(
        model=model,
        skills=config.skills.sources,
        tools=tools or [],
    )
    return agent
