"""
Tablas de mapeo: códigos canónicos del dominio → IDs/códigos de la API de Factus.

Si Factus actualiza sus catálogos, solo se modifica este archivo.
Si se añade otro proveedor (Siigo, Carvajal), se crea un archivo equivalente
específico para ese proveedor.
"""

# Tipo de documento de identificación: código canónico → ID entero de Factus
DOCUMENT_TYPE_TO_FACTUS_ID: dict[str, int] = {
    "RC":             1,  # Registro civil
    "TI":             2,  # Tarjeta de identidad
    "CC":             3,  # Cédula de ciudadanía
    "TE":             4,  # Tarjeta de extranjería
    "CE":             5,  # Cédula de extranjería
    "NIT":            6,  # NIT
    "PASAPORTE":      7,  # Pasaporte
    "DIE":            8,  # Documento de identificación extranjero
    "PEP":            9,  # PEP
    "NIT_EXTRANJERO": 10, # NIT de otro país
    "NUIP":           11, # NUIP
}

# Tipo de organización legal: código canónico → ID entero de Factus
LEGAL_ORGANIZATION_TO_FACTUS_ID: dict[str, int] = {
    "company": 1,  # Persona jurídica
    "person":  2,  # Persona natural
}

# Responsabilidad tributaria de ITEMS: código canónico → ID de Factus
ITEM_TRIBUTE_TO_FACTUS_ID: dict[str, int] = {
    "1": 1,     # IVA
    "2": 2,     # IC
    "3": 3,     # ICA
    "4": 4,     # INC
    "IVA": 1,   # Alias
    "INC": 4,   # Alias
    "ZZ": 21,   # Para items sin tributo, podría ser 21 (Timbre/No aplica)
}

# Responsabilidad tributaria del CLIENTE: código canónico → ID de Factus
CUSTOMER_TRIBUTE_TO_FACTUS_ID: dict[str, int] = {
    "01": 18,   # IVA
    "IVA": 18,  # Alias
    "ZZ": 21,   # No aplica
    "21": 21,   # Alias por si llega directo
}

# Forma de pago: código canónico → código de Factus (string)
PAYMENT_FORM_TO_FACTUS_CODE: dict[str, str] = {
    "cash":   "1",
    "credit": "2",
}

# Tipo de documento tributario: código canónico → código de Factus (string)
DOCUMENT_TYPE_TO_FACTUS_BILL_CODE: dict[str, str] = {
    "invoice": "01",
    "export":  "02",
}

# Concepto de corrección (nota crédito): código canónico → código entero de Factus
CORRECTION_CONCEPT_TO_FACTUS_CODE: dict[str, int] = {
    "partial_return":   1,
    "cancellation":     2,
    "discount":         3,
    "price_adjustment": 4,
    "other":            5,
}

# Códigos de unidad de medida canónicos → ID entero de Factus
UNIT_MEASURE_TO_FACTUS_ID: dict[str, int] = {
    "94": 70,   # unidad
    "70": 70,   # Fallback
    "KGM": 414, # kilogramo
    "LBR": 449, # libra
    "MLT": 499, # mililitro
    "MTR": 512, # metro
    "GLL": 874, # galón
}

# Código estándar de producto → ID entero de Factus
STANDARD_CODE_TO_FACTUS_ID: dict[str, int] = {
    "1": 1, # Estándar de adopción del contribuyente
    "2": 2, # UNSPSC
    "3": 3, # Partida Arancelaria
    "4": 4, # GTIN
}

