"""Configuration loader, persistence helper, and environment validator for BlogForge."""

import os
import logging
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS: Tuple[str, ...] = ("gemini", "anthropic", "openai", "cursor")
DEFAULT_PROVIDER = "gemini"

VALID_THINKING_LEVELS = ("low", "medium", "high")
DEFAULT_THINKING_LEVEL = "medium"

PROVIDER_DEFAULT_MODELS: Dict[str, str] = {
    "gemini": "gemini-3.8-flash",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openai": "gpt-4o",
    "cursor": "cursor-small",
}
DEFAULT_MODEL = PROVIDER_DEFAULT_MODELS["gemini"]


def load_config() -> None:
    """Loads environment variables from local .env."""
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv()


def save_config_value(key: str, value: str, env_path: str = ".env") -> None:
    """Updates or appends a configuration variable in .env and os.environ."""
    os.environ[key] = value
    lines = []
    key_found = False

    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                if line.strip().startswith(f"{key}=") or line.strip().startswith(f"{key} ="):
                    new_lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    new_lines.append(line)
            if not key_found:
                if new_lines and not new_lines[-1].endswith("\n"):
                    new_lines.append("\n")
                new_lines.append(f"{key}={value}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except OSError as e:
            logger.warning(f"Could not persist {key} to {env_path}: {e}")
    else:
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")
        except OSError as e:
            logger.warning(f"Could not create {env_path}: {e}")


def get_active_provider_name() -> str:
    """Returns the active AI provider name ('gemini', 'anthropic', 'openai', 'cursor')."""
    raw_provider = os.getenv("AI_PROVIDER", DEFAULT_PROVIDER).lower().strip()
    if raw_provider in SUPPORTED_PROVIDERS:
        return raw_provider
    if raw_provider == "claude":
        return "anthropic"
    if raw_provider == "chatgpt":
        return "openai"
    if raw_provider in ("custom", "custom_openai", "openrouter"):
        return "cursor"
    return DEFAULT_PROVIDER


def get_active_model(provider: Optional[str] = None) -> str:
    """Retrieves active model for specified provider or active system provider."""
    p_name = provider or get_active_provider_name()
    if p_name == "gemini":
        return os.getenv("GEMINI_MODEL", PROVIDER_DEFAULT_MODELS["gemini"]).strip()
    elif p_name == "anthropic":
        return os.getenv("ANTHROPIC_MODEL", PROVIDER_DEFAULT_MODELS["anthropic"]).strip()
    elif p_name == "openai":
        return os.getenv("OPENAI_MODEL", PROVIDER_DEFAULT_MODELS["openai"]).strip()
    elif p_name == "cursor":
        return os.getenv("CURSOR_MODEL", PROVIDER_DEFAULT_MODELS["cursor"]).strip()
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip()


def get_thinking_level() -> str:
    """Retrieves and validates GEMINI_THINKING_LEVEL.

    Valid values: low, medium, high.
    Note: 'minimal' is unsupported by Gemini 3.8 Flash and will fall back to 'medium'.
    """
    raw_level = os.getenv("GEMINI_THINKING_LEVEL", DEFAULT_THINKING_LEVEL).lower().strip()
    if raw_level in VALID_THINKING_LEVELS:
        return raw_level

    if raw_level == "minimal":
        logger.warning(
            "Thinking level 'minimal' is unsupported by Gemini 3.8 Flash. Falling back to 'medium'."
        )
    else:
        logger.warning(
            f"Invalid GEMINI_THINKING_LEVEL '{raw_level}'. Falling back to default '{DEFAULT_THINKING_LEVEL}'."
        )
    return DEFAULT_THINKING_LEVEL


def get_model() -> str:
    """Retrieves GEMINI_MODEL with default fallback to gemini-3.8-flash."""
    return get_active_model("gemini")
