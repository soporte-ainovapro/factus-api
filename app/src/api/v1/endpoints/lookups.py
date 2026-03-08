from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import List, Optional
from app.src.core.responses import ApiResponse
from app.src.domain.exceptions import FactusAPIError
from app.src.domain.models.lookup import (
    Municipality,
    Tax,
    Unit,
    NumberingRange,
    Country,
    Acquirer,
    ReferenceTables,
    ReferenceEntry,
    ReferenceEntryInt,
    CustomerTributeEntry,
)
from app.src.infrastructure.gateways.factus_lookup_gateway import FactusLookupGateway
from app.src.core.config import settings

from app.src.domain.models.user import User
from app.src.api.deps import get_current_user

router = APIRouter()

# ---------------------------------------------------------------------------
# Tablas de referencia fijas (norma DIAN) — actualizadas desde la documentación
# oficial de Factus: https://developers.factus.com.co/tablas-de-referencia/tablas/
# ---------------------------------------------------------------------------
_REFERENCE_TABLES = ReferenceTables(
    identification_document_types=[
        ReferenceEntryInt(id=1,  name="Registro civil"),
        ReferenceEntryInt(id=2,  name="Tarjeta de identidad"),
        ReferenceEntryInt(id=3,  name="Cédula de ciudadanía"),
        ReferenceEntryInt(id=4,  name="Tarjeta de extranjería"),
        ReferenceEntryInt(id=5,  name="Cédula de extranjería"),
        ReferenceEntryInt(id=6,  name="NIT"),
        ReferenceEntryInt(id=7,  name="Pasaporte"),
        ReferenceEntryInt(id=8,  name="Documento de identificación extranjero"),
        ReferenceEntryInt(id=9,  name="PEP"),
        ReferenceEntryInt(id=10, name="NIT otro país"),
        ReferenceEntryInt(id=11, name="NUIP"),
    ],
    legal_organization_types=[
        ReferenceEntryInt(id=1, name="Persona Jurídica"),
        ReferenceEntryInt(id=2, name="Persona Natural"),
    ],
    customer_tribute_types=[
        CustomerTributeEntry(id=18, code="01", name="IVA"),
        CustomerTributeEntry(id=21, code="ZZ", name="No aplica"),
    ],
    payment_methods=[
        ReferenceEntry(code="10",  name="Efectivo"),
        ReferenceEntry(code="42",  name="Consignación"),
        ReferenceEntry(code="20",  name="Cheque"),
        ReferenceEntry(code="47",  name="Transferencia"),
        ReferenceEntry(code="71",  name="Bonos"),
        ReferenceEntry(code="72",  name="Vales"),
        ReferenceEntry(code="1",   name="Medio de pago no definido"),
        ReferenceEntry(code="49",  name="Tarjeta Débito"),
        ReferenceEntry(code="48",  name="Tarjeta Crédito"),
        ReferenceEntry(code="ZZZ", name="Otro"),
    ],
    payment_forms=[
        ReferenceEntry(code="1", name="Pago de contado"),
        ReferenceEntry(code="2", name="Pago a crédito"),
    ],
    product_standard_codes=[
        ReferenceEntryInt(id=1, name="Estándar de adopción del contribuyente"),
        ReferenceEntryInt(id=2, name="UNSPSC"),
        ReferenceEntryInt(id=3, name="Partida Arancelaria"),
        ReferenceEntryInt(id=4, name="GTIN"),
    ],
    document_types=[
        ReferenceEntry(code="01", name="Factura electrónica de venta"),
        ReferenceEntry(code="03", name="Instrumento electrónico de transmisión - tipo 03"),
    ],
)


def get_lookup_gateway() -> FactusLookupGateway:
    return FactusLookupGateway(base_url=settings.FACTUS_BASE_URL)


@router.get("/reference-tables", response_model=ApiResponse[ReferenceTables])
async def get_reference_tables(
    current_user: User = Depends(get_current_user)
):
    """
    Retorna todas las tablas de referencia fijas definidas por la DIAN.
    No requiere token de Factus — los datos son estáticos y no cambian.
    Incluye: tipos de documento, organización legal, tributos de clientes,
    métodos de pago, formas de pago, estándares de producto y tipos de documento.
    """
    return ApiResponse(
        message="Tablas de referencia obtenidas exitosamente",
        data=_REFERENCE_TABLES
    )


@router.get("/municipalities", response_model=ApiResponse[List[Municipality]])
async def get_municipalities(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_municipalities(x_factus_token)
        return ApiResponse(message="Municipios obtenidos exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/taxes", response_model=ApiResponse[List[Tax]])
async def get_taxes(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_tax_types(x_factus_token)
        return ApiResponse(message="Tipos de impuesto obtenidos exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/units", response_model=ApiResponse[List[Unit]])
async def get_units(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_units(x_factus_token)
        return ApiResponse(message="Unidades obtenidas exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/numbering-ranges", response_model=ApiResponse[List[NumberingRange]])
async def get_numbering_ranges(
    x_factus_token: str = Header(...),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_numbering_ranges(x_factus_token)
        return ApiResponse(message="Rangos de numeración obtenidos exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/countries", response_model=ApiResponse[List[Country]])
async def get_countries(
    x_factus_token: str = Header(...),
    name: Optional[str] = Query(None, description="Filtrar por nombre del país"),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    try:
        data = await gateway.get_countries(x_factus_token, name=name)
        return ApiResponse(message="Países obtenidos exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/acquirer", response_model=ApiResponse[Acquirer])
async def get_acquirer(
    x_factus_token: str = Header(...),
    identification_document_id: int = Query(
        ..., description="ID del tipo de documento de identidad (ver /reference-tables)"
    ),
    identification_number: str = Query(
        ..., description="Número de documento del adquiriente"
    ),
    gateway: FactusLookupGateway = Depends(get_lookup_gateway),
    current_user: User = Depends(get_current_user)
):
    """
    Consulta nombre y correo de un adquiriente directamente en la DIAN,
    dado su tipo y número de documento. Útil para autocompletar datos del cliente.
    """
    try:
        data = await gateway.get_acquirer(
            x_factus_token,
            identification_document_id=identification_document_id,
            identification_number=identification_number
        )
        return ApiResponse(message="Datos del adquiriente obtenidos exitosamente", data=data)
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
