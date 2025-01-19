"""Exceptions for Dynamic DNS integration."""

class DynamicDNSError(Exception):
    """Base exception for Dynamic DNS."""
    pass

class AuthenticationError(DynamicDNSError):
    """Authentication failed."""
    pass

class ConnectionError(DynamicDNSError):
    """Connection failed."""
    pass

class ConfigurationError(DynamicDNSError):
    """Configuration error."""
    pass

class UpdateError(DynamicDNSError):
    """Update failed."""
    pass

class ResolutionError(DynamicDNSError):
    """DNS resolution failed."""
    pass 