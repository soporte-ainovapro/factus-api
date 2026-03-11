from abc import ABC, abstractmethod
from app.domain.models.company import CompanyResponse, CompanyUpdate, CompanyLogoUpdateResponse

class ICompanyGateway(ABC):
    @abstractmethod
    async def get_company(self, token: str) -> CompanyResponse:
        """
        Gets the information of the company associated with the user.
        """
        pass

    @abstractmethod
    async def update_company(self, company: CompanyUpdate, token: str) -> CompanyResponse:
        """
        Updates the information of the company associated with the user.
        """
        pass

    @abstractmethod
    async def update_company_logo(self, file_name: str, file_content: bytes, file_content_type: str, token: str) -> CompanyLogoUpdateResponse:
        """
        Updates the logo of the company associated with the user.
        """
        pass
