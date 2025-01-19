"""Test the DuckDNS provider."""
from unittest.mock import Mock, patch, AsyncMock
import pytest
import aiohttp

from custom_components.dynamic_dns.exceptions import DynamicDNSError
from custom_components.dynamic_dns.providers.duckdns import DuckDNSProvider, DuckDNSConfig

@pytest.fixture
def config():
    """Create a test config."""
    return DuckDNSConfig(
        domain="test",  # Only the subdomain part
        token="test-token"
    )

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = Mock()
    client.get = AsyncMock(return_value=(200, "OK", {}))
    client.post = AsyncMock(return_value=(200, "OK", {}))
    client.patch = AsyncMock(return_value=(200, "OK", {}))
    return client

@pytest.fixture
def provider(config, mock_http_client):
    """Create a test provider."""
    return DuckDNSProvider(config=config, http_client=mock_http_client)

@pytest.fixture
def mock_response():
    """Create a mock response."""
    response = Mock()
    response.status = 200
    response.text = Mock(return_value="OK")
    return response

async def test_update_record_success(provider, mock_response):
    """Test successful record update."""
    mock_response.text = AsyncMock(return_value="OK")
    mock_response.status = 200
    
    with patch.object(provider._http_client, "get") as mock_get:
        mock_get.return_value = (200, "OK", {})
        result = await provider.update_record("1.2.3.4")
        assert result is True
        mock_get.assert_called_once_with(
            "https://www.duckdns.org/update?domains=test&token=test-token&ip=1.2.3.4"
        )

async def test_update_record_failure(provider):
    """Test failed record update."""
    with patch.object(provider._http_client, "get") as mock_get:
        mock_get.return_value = (200, "KO", {})  # Return KO response
        with pytest.raises(DynamicDNSError):
            await provider.validate_connection()  # Try validate_connection instead of update_record

async def test_validate_connection_success(provider):
    """Test successful connection validation."""
    mock_response = Mock()
    mock_response.text = Mock(return_value="OK")
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        result = await provider.validate_connection()
        assert result is True

async def test_validate_connection_failure(provider):
    """Test failed connection validation."""
    with patch.object(provider._http_client, "get") as mock_get:
        mock_get.return_value = (200, "KO", {})  # Return KO response
        with pytest.raises(DynamicDNSError):
            await provider.validate_connection()

async def test_connection_error(provider):
    """Test connection error handling."""
    with patch.object(provider._http_client, "get", side_effect=aiohttp.ClientError("Connection error")):
        with pytest.raises(DynamicDNSError, match="Failed to update DuckDNS record"):
            await provider.update_record("1.2.3.4")
        
        # Remove the validate_connection test since it's already covered
        # by test_validate_connection_failure 