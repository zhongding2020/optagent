from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
import yaml


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key_env: str = "OPENAI_API_KEY"


class EmbeddingConfig(BaseModel):
    provider: str = "huggingface"
    model: str = "BAAI/bge-small-zh-v1.5"
    device: str = "cpu"


class KBConfig(BaseModel):
    chroma_persist_dir: str = "./data/chroma"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    default_top_k: int = 5


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8020


class PersistenceConfig(BaseModel):
    sqlite_path: str = "./data/sessions.db"
    checkpoint_dir: str = "./data/checkpoints"


class SkillsConfig(BaseModel):
    sources: list[str] = ["./skills"]


class WorkflowsConfig(BaseModel):
    directory: str = "./workflows"
    default: str = "process-optimization"


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    knowledge_base: KBConfig = Field(default_factory=KBConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    workflows: WorkflowsConfig = Field(default_factory=WorkflowsConfig)

    @classmethod
    def load(cls, path: str = "./config.yaml") -> "AppConfig":
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p) as f:
            data = yaml.safe_load(f)
        if data is None:
            return cls()
        return cls(**data)
