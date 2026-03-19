from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import List, Optional
from app.core.exceptions import FactusAPIError
from app.schemas.lookup import (
    Municipality,
    Tax,
    Unit,
    Country,
    Acquirer,
    ReferenceTables,
    ReferenceEntry,
    ReferenceEntryInt,
)
from app.services.interfaces import LookupService
from app.api.deps import verify_api_key, get_lookup_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Tablas de referencia fijas (norma DIAN) — actualizadas desde la documentación
# oficial de Factus: https://developers.factus.com.co/tablas-de-referencia/tablas/
# ---------------------------------------------------------------------------
_REFERENCE_TABLES = ReferenceTables(
    identification_document_types=[
        ReferenceEntry(code="RC", name="Registro civil"),
        ReferenceEntry(code="TI", name="Tarjeta de identidad"),
        ReferenceEntry(code="CC", name="Cédula de ciudadanía"),
        ReferenceEntry(code="TE", name="Tarjeta de extranjería"),
        ReferenceEntry(code="CE", name="Cédula de extranjería"),
        ReferenceEntry(code="NIT", name="NIT"),
        ReferenceEntry(code="PASAPORTE", name="Pasaporte"),
        ReferenceEntry(code="DIE", name="Documento de identificación extranjero"),
        ReferenceEntry(code="PEP", name="PEP"),
        ReferenceEntry(code="NIT_EXTRANJERO", name="NIT otro país"),
        ReferenceEntry(code="NUIP", name="NUIP"),
    ],
    legal_organization_types=[
        ReferenceEntry(code="company", name="Persona Jurídica"),
        ReferenceEntry(code="person", name="Persona Natural"),
    ],
    customer_tribute_types=[
        ReferenceEntry(code="IVA", name="IVA"),
        ReferenceEntry(code="ZZ", name="No aplica"),
    ],
    payment_methods=[
        ReferenceEntry(code="cash_payment", name="Efectivo"),
        ReferenceEntry(code="transfer", name="Consignación / Transferencia"),
        ReferenceEntry(code="check", name="Cheque"),
        ReferenceEntry(code="debit_card", name="Tarjeta Débito"),
        ReferenceEntry(code="credit_card", name="Tarjeta Crédito"),
        ReferenceEntry(code="cash_savings", name="Ahorro"),
        ReferenceEntry(code="other", name="Otro"),
    ],
    payment_forms=[
        ReferenceEntry(code="cash", name="Pago de contado"),
        ReferenceEntry(code="credit", name="Pago a crédito"),
    ],
    product_standard_codes=[
        ReferenceEntryInt(id=1, name="Estándar de adopción del contribuyente"),
        ReferenceEntryInt(id=2, name="UNSPSC"),
        ReferenceEntryInt(id=3, name="Partida Arancelaria"),
        ReferenceEntryInt(id=4, name="GTIN"),
    ],
    document_types=[
        ReferenceEntry(code="01", name="Factura electrónica de venta"),
        ReferenceEntry(
            code="03", name="Instrumento electrónico de transmisión - tipo 03"
        ),
    ],
)


@router.get("/reference-tables", response_model=ReferenceTables)
async def get_reference_tables(_: str = Depends(verify_api_key)):
    """
    Retorna todas las tablas de referencia fijas definidas por la DIAN.
    No requiere token de Factus — los datos son estáticos y no cambian.
    Incluye: tipos de documento, organización legal, tributos de clientes,
    métodos de pago, formas de pago, estándares de producto y tipos de documento.
    """
    return _REFERENCE_TABLES


@router.get("/municipalities", response_model=List[Municipality])
async def get_municipalities(
    x_factus_token: str = Header(...),
    service: LookupService = Depends(get_lookup_service),
    _: str = Depends(verify_api_key),
):
    try:
        data = await service.get_municipalities(x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/taxes", response_model=List[Tax])
async def get_taxes(
    x_factus_token: str = Header(...),
    service: LookupService = Depends(get_lookup_service),
    _: str = Depends(verify_api_key),
):
    try:
        data = await service.get_tax_types(x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/units", response_model=List[Unit])
async def get_units(
    x_factus_token: str = Header(...),
    service: LookupService = Depends(get_lookup_service),
    _: str = Depends(verify_api_key),
):
    try:
        data = await service.get_units(x_factus_token)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/countries", response_model=List[Country])
async def get_countries(
    x_factus_token: str = Header(...),
    name: Optional[str] = Query(None, description="Filtrar por nombre del país"),
    service: LookupService = Depends(get_lookup_service),
    _: str = Depends(verify_api_key),
):
    try:
        data = await service.get_countries(x_factus_token, name=name)
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/acquirer", response_model=Acquirer)
async def get_acquirer(
    x_factus_token: str = Header(...),
    identification_document_type: str = Query(
        ...,
        description=(
            "Código canónico del tipo de documento (ej: 'CC', 'NIT', 'TI'). "
            "Ver /reference-tables."
        ),
    ),
    identification_number: str = Query(
        ..., description="Número de documento del adquiriente"
    ),
    service: LookupService = Depends(get_lookup_service),
    _: str = Depends(verify_api_key),
):
    """
    Consulta nombre y correo de un adquiriente directamente en la DIAN,
    dado su tipo y número de documento. Útil para autocompletar datos del cliente.
    """
    try:
        data = await service.get_acquirer(
            x_factus_token,
            identification_document_type=identification_document_type,
            identification_number=identification_number,
        )
        return data
    except FactusAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
