from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

DataT = TypeVar("DataT")

class ApiResponse(BaseModel, Generic[DataT]):
    """
    Clase genérica para estandarizar las respuestas de los endpoints.

    Ejemplo de uso en un endpoint:
        @router.post("/", response_model=ApiResponse[InvoiceResponse])
        async def create_invoice(...):
            data = await gateway.create_invoice(invoice, x_factus_token)
            return ApiResponse(
                success=True, 
                message="Factura creada", 
                data=data
            )
    """
    success: bool = True
    message: str = "Operación exitosa"
    data: Optional[DataT] = None
    errors: Optional[Any] = None
