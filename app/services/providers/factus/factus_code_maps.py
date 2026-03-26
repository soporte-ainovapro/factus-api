"""
Tablas de mapeo: códigos canónicos del dominio → IDs/códigos de la API de Factus.

Si Factus actualiza sus catálogos, solo se modifica este archivo.
Si se añade otro proveedor (Siigo, Carvajal), se crea un archivo equivalente
específico para ese proveedor.
"""

# Tipo de documento de identificación: código canónico → ID entero de Factus
DOCUMENT_TYPE_TO_FACTUS_ID: dict[str, int] = {
    "RC": 1,  # Registro civil
    "TI": 2,  # Tarjeta de identidad
    "CC": 3,  # Cédula de ciudadanía
    "TE": 4,  # Tarjeta de extranjería
    "CE": 5,  # Cédula de extranjería
    "NIT": 6,  # NIT
    "PASAPORTE": 7,  # Pasaporte
    "DIE": 8,  # Documento de identificación extranjero
    "PEP": 9,  # PEP
    "NIT_EXTRANJERO": 10,  # NIT de otro país
    "NUIP": 11,  # NUIP
    "CONS_FINAL": 13, # Consumidor Final
}

# Tipo de organización legal: código canónico → ID entero de Factus
LEGAL_ORGANIZATION_TO_FACTUS_ID: dict[str, int] = {
    "company": 1,  # Persona jurídica
    "person": 2,  # Persona natural
}

# Responsabilidad tributaria de ITEMS: código canónico → ID de Factus
ITEM_TRIBUTE_TO_FACTUS_ID: dict[str, int] = {
    "1": 1,  # IVA
    "2": 2,  # IC
    "3": 3,  # ICA
    "4": 4,  # INC
    "IVA": 1,  # Alias
    "INC": 4,  # Alias
    "ZZ": 21,  # Para items sin tributo, podría ser 21 (Timbre/No aplica)
}

# Responsabilidad tributaria del CLIENTE: código canónico → ID de Factus
CUSTOMER_TRIBUTE_TO_FACTUS_ID: dict[str, int] = {
    "IVA": 18,  # IVA
    "ZZ": 21,  # No aplica
}

# Método de pago: código canónico -> código de Factus (string)
PAYMENT_METHOD_TO_FACTUS_CODE: dict[str, str] = {
    "cash_payment": "10",
    "transfer": "47",
    "check": "20",
    "debit_card": "49",
    "credit_card": "48",
    "cash_savings": "42",
    "other": "ZZZ",
}

# Forma de pago: código canónico → código de Factus (string)
PAYMENT_FORM_TO_FACTUS_CODE: dict[str, str] = {
    "cash": "1",
    "credit": "2",
}

# Tipo de documento tributario: código canónico → código de Factus (string)
DOCUMENT_TYPE_TO_FACTUS_BILL_CODE: dict[str, str] = {
    "invoice": "01",
    "export": "02",
}

# Códigos de unidad de medida canónicos → ID entero de Factus
UNIT_MEASURE_TO_FACTUS_ID: dict[str, int] = {
    "94": 70,  # unidad
    "70": 70,  # Fallback
    "KGM": 414,  # kilogramo
    "LBR": 449,  # libra
    "MLT": 499,  # mililitro
    "MTR": 512,  # metro
    "GLL": 874,  # galón
}

# Código estándar de producto → ID entero de Factus
STANDARD_CODE_TO_FACTUS_ID: dict[str, int] = {
    "1": 1,  # Estándar de adopción del contribuyente
    "2": 2,  # UNSPSC
    "3": 3,  # Partida Arancelaria
    "4": 4,  # GTIN
}

# Códigos de tipo de operación (Notas Crédito) → código de Factus (string)
CREDIT_NOTE_OPERATION_TYPE_TO_FACTUS_CODE: dict[str, str] = {
    "20": "20",  # Nota Crédito que referencia una factura electrónica.
    "22": "22",  # Nota Crédito sin referencia a una factura electrónica.
}

# Códigos de concepto de corrección (Notas Crédito) → código de Factus (string)
CREDIT_NOTE_CORRECTION_CONCEPT_TO_FACTUS_CODE: dict[str, str] = {
    "1": "1",  # Devolución parcial de los bienes y/o no aceptación parcial del servicio.
    "2": "2",  # Anulación de factura electrónica.
    "3": "3",  # Rebaja o descuento parcial o total.
    "4": "4",  # Ajuste de precio.
    "5": "5",  # Descuento comercial por pronto pago.
    "6": "6",  # Descuento comercial por volumen de ventas.
}
