from unittest.mock import AsyncMock, patch
import pytest
from app.domain.models.company import CompanyUpdate

@pytest.fixture
def company_gateway_mock():
    with patch('app.api.v1.endpoints.company.FactusCompanyGateway') as MockGateway:
        mock_instance = MockGateway.return_value
        # Mock implementations
        mock_instance.get_company = AsyncMock()
        mock_instance.update_company = AsyncMock()
        mock_instance.update_company_logo = AsyncMock()
        yield mock_instance

@pytest.fixture
def mock_get_company_gateway(company_gateway_mock):
    # This fixture replaces the dependency
    from app.api.v1.endpoints.company import get_company_gateway as base_get_company_gateway
    with patch('app.api.v1.endpoints.company.get_company_gateway', return_value=company_gateway_mock):
        yield company_gateway_mock
