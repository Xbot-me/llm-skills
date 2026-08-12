"""Env loading and small config helpers shared by the harness."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str

    def __str__(self) -> str:
        return f"{self.provider}:{self.model}"

    @property
    def slug(self) -> str:
        """Filesystem-safe identifier for report filenames."""
        return f"{self.provider}-{self.model}".replace("/", "_")


def parse_model_specs(raw: str) -> list[ModelSpec]:
    """Parse 'provider:model,provider:model' into ModelSpec objects."""
    specs = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise ValueError(
                f"Model spec '{chunk}' must be in 'provider:model' form, "
                f"e.g. 'anthropic:claude-sonnet-4-5'."
            )
        provider, model = chunk.split(":", 1)
        specs.append(ModelSpec(provider=provider.strip(), model=model.strip()))
    return specs


def default_models() -> list[ModelSpec]:
    raw = os.environ.get("DEFAULT_MODELS", "")
    if not raw:
        raise RuntimeError(
            "No --models given and DEFAULT_MODELS is not set in .env. "
            "Set one or pass --models explicitly."
        )
    return parse_model_specs(raw)


def judge_spec() -> ModelSpec:
    provider = os.environ.get("JUDGE_PROVIDER", "anthropic")
    model = os.environ.get("JUDGE_MODEL", "")
    if not model:
        raise RuntimeError("JUDGE_MODEL is not set in .env.")
    return ModelSpec(provider=provider, model=model)


def key_available(provider: str) -> bool:
    key_var = {
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
    }.get(provider)
    if key_var is None:
        return False
    return bool(os.environ.get(key_var))
