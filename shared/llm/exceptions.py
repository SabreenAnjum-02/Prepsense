from shared.error_handler import RetryableError, TerminalError

class LLMConnectionError(RetryableError):
    """Raised when the LLM service is unreachable."""
    pass

class LLMTimeoutError(RetryableError):
    """Raised when an LLM request times out."""
    pass

class LLMFormatError(RetryableError):
    """Raised when the LLM returns invalid JSON or unstructured text when structured was required."""
    pass

class LLMConfigurationError(TerminalError):
    """Raised when the LLM service is improperly configured."""
    pass
