"""Custom exception classes for BlogForge."""


class BlogForgeError(Exception):
    """Base exception for all BlogForge errors."""
    pass


class ConfigurationError(BlogForgeError):
    """Raised when there is an invalid or missing configuration."""
    pass


class ProviderError(BlogForgeError):
    """Base exception for external AI and search provider errors."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Raised when credentials or API keys are missing or invalid."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limits or quotas are exceeded."""
    pass


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an unparseable or unexpected response."""
    pass


class ProviderServiceUnavailableError(ProviderError):
    """Raised when a provider service is temporarily unreachable or returning 5xx errors."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""
    pass
