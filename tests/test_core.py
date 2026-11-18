"""Unit and boundary tests for core application configuration, logging, constants, and exceptions."""

import os
import logging
from app.core import constants
from app.core.config import load_config, get_thinking_level, get_model
from app.core.logging import setup_logging
from app.core.exceptions import (
    BlogForgeError,
    ConfigurationError,
    ProviderError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderServiceUnavailableError,
    ProviderTimeoutError,
)


def test_constants():
    """Verify core application constants are defined and non-empty."""
    assert hasattr(constants, "APP_NAME")
    assert constants.APP_NAME == "BlogForge"
    assert hasattr(constants, "APP_VERSION")
    assert constants.APP_VERSION == "1.0.0"


def test_config_loader_with_env_file(tmp_path, monkeypatch):
    """Verify load_config loads variables from .env file into environment."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Comment line\n"
        "BLOGFORGE_CUSTOM_KEY=alpha_test_val\n"
        "EMPTY_VAL=\n"
        "SPACED_KEY=  trimmed_val  \n",
        encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    load_config()

    assert os.getenv("BLOGFORGE_CUSTOM_KEY") == "alpha_test_val"
    assert os.getenv("EMPTY_VAL") == ""
    assert os.getenv("SPACED_KEY") == "trimmed_val"


def test_config_loader_without_env_file(tmp_path, monkeypatch):
    """Verify load_config behaves gracefully when no .env file exists."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    monkeypatch.chdir(empty_dir)
    # Should not raise exception
    load_config()


def test_setup_logging_initialization(tmp_path, monkeypatch):
    """Verify setup_logging configures root logger handlers and log file."""
    monkeypatch.chdir(tmp_path)

    # Clear root handlers first for isolated test
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    root.handlers.clear()

    try:
        setup_logging("DEBUG")
        assert root.level == logging.DEBUG
        assert len(root.handlers) >= 2  # StreamHandler + FileHandler

        log_file = tmp_path / "logs" / "blogforge.log"
        assert log_file.exists()

        test_logger = logging.getLogger("test_core")
        test_logger.debug("Debug test message")
        test_logger.info("Info test message")

        # Flush handlers
        for h in root.handlers:
            h.flush()

        content = log_file.read_text(encoding="utf-8")
        assert "Debug test message" in content
        assert "Info test message" in content

        # Test duplicate setup call does not add more handlers
        num_handlers = len(root.handlers)
        setup_logging("INFO")
        assert len(root.handlers) == num_handlers
    finally:
        # Restore root handlers
        for h in root.handlers:
            h.close()
        root.handlers = original_handlers


def test_setup_logging_fallback_level(tmp_path, monkeypatch):
    """Verify setup_logging defaults to INFO when invalid level is passed."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOG_LEVEL", "INVALID_LEVEL")

    root = logging.getLogger()
    original_handlers = root.handlers[:]
    root.handlers.clear()

    try:
        setup_logging(None)
        assert root.level == logging.INFO
    finally:
        for h in root.handlers:
            h.close()
        root.handlers = original_handlers


def test_exception_hierarchy():
    """Verify complete exception inheritance tree and instantiations."""
    assert issubclass(ConfigurationError, BlogForgeError)
    assert issubclass(ProviderError, BlogForgeError)
    assert issubclass(ProviderAuthenticationError, ProviderError)
    assert issubclass(ProviderRateLimitError, ProviderError)
    assert issubclass(ProviderResponseError, ProviderError)
    assert issubclass(ProviderServiceUnavailableError, ProviderError)
    assert issubclass(ProviderTimeoutError, ProviderError)

    for exc_cls in [
        BlogForgeError,
        ConfigurationError,
        ProviderError,
        ProviderAuthenticationError,
        ProviderRateLimitError,
        ProviderResponseError,
        ProviderServiceUnavailableError,
        ProviderTimeoutError,
    ]:
        err = exc_cls("Test error message")
        assert str(err) == "Test error message"
        assert isinstance(err, BlogForgeError)


def test_config_thinking_level_and_model(monkeypatch):
    """Verify get_thinking_level and get_model return defaults and validate inputs."""
    monkeypatch.delenv("GEMINI_THINKING_LEVEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    # Defaults
    assert get_thinking_level() == "medium"
    assert get_model() == "gemini-3.8-flash"

    # Valid thinking levels
    for lvl in ["low", "medium", "high"]:
        monkeypatch.setenv("GEMINI_THINKING_LEVEL", lvl)
        assert get_thinking_level() == lvl

    # Minimal is unsupported, falls back to medium
    monkeypatch.setenv("GEMINI_THINKING_LEVEL", "minimal")
    assert get_thinking_level() == "medium"

    # Invalid thinking level falls back to medium
    monkeypatch.setenv("GEMINI_THINKING_LEVEL", "ultra_high")
    assert get_thinking_level() == "medium"

    # Custom model
    monkeypatch.setenv("GEMINI_MODEL", "gemini-4-carbon")
    assert get_model() == "gemini-4-carbon"
