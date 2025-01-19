"""Test the DNSimple provider."""
from unittest.mock import Mock, patch, AsyncMock
import pytest
import aiohttp

from custom_components.dynamic_dns.exceptions import (
    AuthenticationError,
    ConfigurationError,
    DynamicDNSError,
    UpdateError
)
from custom_components.dynamic_dns.providers.dnsimple import DNSimpleProvider, DNSimpleConfig

@pytest.fixture
def config():
    """Create a test config."""
    return DNSimpleConfig(
        token="test-token",
        account_id="67890",
        zone="example.com",
        record_name="12345"
    )

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = Mock()
    # Fix whoami response
    client.get = AsyncMock(side_effect=[
        # First call for validate_connection (whoami)
        (200, "OK", {
            "data": {
                "account": {"id": "67890"}
            }
        }),
        # Second call for update_record (get records)
        (200, "OK", {
            "data": [
                {"id": "12345", "name": "test", "type": "A"}
            ]
        })
    ])
    client.post = AsyncMock(return_value=(201, "OK", {}))
    client.patch = AsyncMock(return_value=(200, "OK", {}))
    return client

@pytest.fixture
def provider(config, mock_http_client):
    """Create a test provider."""
    return DNSimpleProvider(config=config, http_client=mock_http_client)

@pytest.fixture
def mock_response():
    """Create a mock response."""
    response = Mock()
    response.status = 200
    response.json = AsyncMock(return_value={
        "data": {
            "account": {"id": "67890"},
            "records": [
                {"id": "12345", "name": "test", "type": "A"}
            ]
        }
    })
    return response

async def test_update_record_success(provider, mock_response):
    """Test successful record update."""
    with patch.object(provider._http_client, "get") as mock_get:
        mock_get.return_value = (200, "OK", {
            "data": [
                {"id": "12345", "name": "test", "type": "A"}
            ]
        })
        result = await provider.update_record("1.2.3.4")
        assert result is True

async def test_update_record_failure(provider):
    """Test failed record update."""
    mock_response = Mock()
    mock_response.status = 404
    
    with patch("aiohttp.ClientSession.patch") as mock_patch:
        mock_patch.return_value.__aenter__.return_value = mock_response
        with pytest.raises(UpdateError):
            await provider.update_record("1.2.3.4")

async def test_validate_connection_success(provider):
    """Test successful connection validation."""
    mock_response = Mock()
    mock_response.status = 200
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        result = await provider.validate_connection()
        assert result is True

async def test_validate_connection_failure(provider):
    """Test failed connection validation."""
    with patch.object(provider._http_client, "get") as mock_get:
        mock_get.return_value = (401, "Unauthorized", {})  # Return 401 status
        with pytest.raises(AuthenticationError):
            await provider.validate_connection() 