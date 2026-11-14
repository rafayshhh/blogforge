"""Configuration loader from .env file."""

from dotenv import load_dotenv, find_dotenv


def load_config() -> None:
    """Loads environment variables from local .env."""
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv()
