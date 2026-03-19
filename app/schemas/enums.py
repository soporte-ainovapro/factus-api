"""
Enums del dominio de facturación electrónica (agnósticos al proveedor).

El adaptador de cada proveedor es responsable de traducir estos valores
a los códigos/IDs que ese proveedor espera.
"""

from enum import Enum


class DocumentType(str, Enum):
    """Tipo de documento tributario emitido."""

    INVOICE = "invoice"  # Factura de venta electrónica
    EXPORT_INVOICE = "export"  # Factura de exportación


class PaymentForm(str, Enum):
    """Forma de pago."""

    CASH = "cash"  # Contado
    CREDIT = "credit"  # Crédito


class IdentificationDocumentType(str, Enum):
    """Tipo de documento de identificación del cliente."""

    CC = "CC"  # Cédula de ciudadanía
    NIT = "NIT"  # NIT
    CE = "CE"  # Cédula de extranjería
    TI = "TI"  # Tarjeta de identidad
    PASPORT = "PASAPORTE"  # Pasaporte
    RC = "RC"  # Registro civil
    TE = "TE"  # Tarjeta de extranjería
    NIT_EXTRANJERO = "NIT_EXTRANJERO"  # NIT de otro país
    NUIP = "NUIP"  # NUIP


class LegalOrganizationType(str, Enum):
    """Tipo de organización legal del cliente."""

    COMPANY = "company"  # Persona jurídica
    PERSON = "person"  # Persona natural


class TributeType(str, Enum):
    """Tipo de tributo / régimen fiscal."""

    IVA = "IVA"  # Responsable de IVA
    NO_APLICA = "ZZ"  # No responsable de IVA / consumidor final
    INC = "INC"  # Impuesto Nacional al Consumo
    IVA_INC = "IVA_INC"  # IVA e INC
