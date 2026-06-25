from typing import Any
from deepagents import create_deep_agent
from deepagents.middleware import (
    create_skills_middleware,
    create_filesystem_middleware,
)
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel

from ..config import AppConfig


def _resolve_model(config: AppConfig) -> BaseChatModel:
    provider = config.llm.provider
    model = config.llm.model
    if provider == "openai":
        return ChatOpenAI(model=model)
    elif provider == "anthropic":
        return ChatAnthropic(model=model)
    elif provider == "ollama":
        return ChatOllama(model=model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def create_optagent_agent(config: AppConfig) -> Any:
    """Create a deepagents agent with skills + filesystem middleware."""
    model = _resolve_model(config)

    skills_middleware = create_skills_middleware(
        backend={"type": "filesystem", "root": "/"},
        sources=config.skills.sources,
    )
    fs_middleware = create_filesystem_middleware(
        backend={"type": "filesystem", "root": "/"},
    )

    agent = create_deep_agent(
        model=model,
        middleware=[skills_middleware, fs_middleware],
    )
    return agent
