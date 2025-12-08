"""Tests for ha_services/system_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import ServiceCall

from smart_heating.ha_services.system_handlers import async_handle_refresh


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_service_call():
    """Create mock service call."""
    return MagicMock(spec=ServiceCall)


class TestSystemHandlers:
    """Test system service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_refresh(self, mock_service_call, mock_coordinator):
        """Test refresh service handler."""
        await async_handle_refresh(mock_service_call, mock_coordinator)
        
        # Verify coordinator refresh was called
        mock_coordinator.async_request_refresh.assert_called_once()
