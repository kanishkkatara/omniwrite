"""
OmniWrite — Pydantic Settings & Configuration Loader
Merges: config.yaml → .env → environment variables (env vars win)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_dotenv_manually() -> None:
    """Manually parse .env and load keys into os.environ for LiteLLM."""
    env_path = Path(".env")
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if val.startswith(('"', "'")) and val.endswith(('"', "'")):
                    val = val[1:-1]
                if key and val:
                    os.environ[key] = val


load_dotenv_manually()


class ModelConfig(BaseSettings):
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    base_url: str | None = None


class SearchProviderConfig(BaseSettings):
    name: str
    enabled: bool = True
    api_key: str | None = None
    max_results: int = 8


class PublisherConfig(BaseSettings):
    enabled: bool = False
    # Fields vary by publisher; stored as raw dict
    model_config = SettingsConfigDict(extra="allow")


class LangSmithConfig(BaseSettings):
    enabled: bool = False
    api_key: str | None = None
    project: str = "omniwrite"


class ObservabilityConfig(BaseSettings):
    langsmith: LangSmithConfig = Field(default_factory=LangSmithConfig)
    prometheus_enabled: bool = True
    otlp_enabled: bool = False
    otlp_endpoint: str = "http://localhost:4317"
    show_cost_summary: bool = True


class ContentLengthSpec(BaseSettings):
    min_words: int
    max_words: int


class GenerationConfig(BaseSettings):
    default_platforms: list[str] = ["blog", "linkedin", "reddit"]
    default_language: str = "en"
    default_length: str = "medium"
    outline_approval_enabled: bool = True
    default_variants: int = 1
    content_lengths: dict[str, ContentLengthSpec] = Field(
        default_factory=lambda: {
            "short": ContentLengthSpec(min_words=300, max_words=600),
            "medium": ContentLengthSpec(min_words=700, max_words=1200),
            "long": ContentLengthSpec(min_words=1500, max_words=2500),
        }
    )


class Settings(BaseSettings):
    """
    Master settings object.
    Priority (highest → lowest):
      1. Environment variables
      2. .env file
      3. config.yaml
      4. Defaults below
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OMNIWRITE_",
        extra="ignore",
        case_sensitive=False,
    )

    # ── API Keys (no prefix — standard env var names) ────────────────────────
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    brave_search_api_key: str | None = Field(default=None, alias="BRAVE_SEARCH_API_KEY")
    langchain_api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")

    # ── App settings (OMNIWRITE_ prefix) ────────────────────────────────────
    debug: bool = False
    log_level: str = "INFO"
    default_mode: str = "test"  # test | production | local | groq
    config_file: str = "config.yaml"

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./omniwrite.db",
        alias="DATABASE_URL",
    )

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_enabled: bool = False

    # ── Derived config from YAML ───────────────────────────────────────────────
    # Populated by load_yaml_config() after instantiation
    models: dict[str, ModelConfig] = Field(
        default_factory=lambda: {
            "test": ModelConfig(model="gpt-4.1-nano"),
            "production": ModelConfig(model="claude-sonnet-4-5", max_tokens=8192),
        }
    )
    agent_models: dict[str, str] = Field(
        default_factory=lambda: {
            "editor": "production",
            "research": "test",
            "brief_extractor": "test",
            "strategy": "test",
            "outline": "test",
        }
    )
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    enabled_platforms: list[str] = ["blog", "reddit", "linkedin", "linkedin_comment"]
    research_enabled: bool = True

    @field_validator("default_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        allowed = {"test", "production", "local", "groq", "custom"}
        if v not in allowed:
            raise ValueError(f"default_mode must be one of {allowed}")
        return v

    def get_model_config(self, agent_name: str | None = None) -> ModelConfig:
        """Return the ModelConfig for the given agent (falls back to default_mode)."""
        mode = self.default_mode
        if agent_name and agent_name in self.agent_models:
            mode = self.agent_models[agent_name]
        return self.models.get(mode, self.models["test"])

    def has_llm_key(self) -> bool:
        return bool(self.openai_api_key or self.anthropic_api_key)


def _resolve_env_refs(obj: Any) -> Any:
    """Recursively resolve ${ENV_VAR} references in YAML values."""
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            var = obj[2:-1]
            return os.environ.get(var)
        return obj
    if isinstance(obj, dict):
        return {k: _resolve_env_refs(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_refs(i) for i in obj]
    return obj


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    return _resolve_env_refs(raw)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance, merged with config.yaml."""
    settings = Settings()

    # Load and merge config.yaml
    config_path = Path(settings.config_file)
    yaml_data = _load_yaml(config_path)

    if not yaml_data:
        # Fall back to config.example.yaml for first-run experience
        yaml_data = _load_yaml(Path("config.example.yaml"))

    # Merge YAML → settings fields
    if "models" in yaml_data:
        parsed_models: dict[str, ModelConfig] = {}
        for name, cfg in yaml_data["models"].items():
            if isinstance(cfg, dict):
                parsed_models[name] = ModelConfig(**cfg)
        if parsed_models:
            settings.models = parsed_models

    if "agent_models" in yaml_data:
        settings.agent_models = yaml_data["agent_models"]

    if "generation" in yaml_data:
        gen = yaml_data["generation"]
        settings.generation = GenerationConfig(
            **{k: v for k, v in gen.items() if k in GenerationConfig.model_fields}
        )

    if yaml_data.get("search", {}).get("research_enabled") is not None:
        settings.research_enabled = yaml_data["search"]["research_enabled"]

    if "plugins" in yaml_data:
        settings.enabled_platforms = yaml_data["plugins"].get(
            "enabled_platforms", settings.enabled_platforms
        )

    # Configure LangSmith if key provided
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.observability.langsmith.project

    return settings
