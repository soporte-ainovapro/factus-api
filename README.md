# Factus API

REST API built with FastAPI that acts as a secure intermediary for the [Factus](https://factus.com.co) Colombian e-invoicing platform. It exposes authenticated endpoints for creating, querying, downloading, and managing electronic invoices validated by the DIAN.

## Features

- JWT-based local authentication
- Full Factus OAuth2 token lifecycle (login + refresh)
- Company profile management (view, update, logo update)
- Numbering Ranges management (CRUD operations)
- Invoice creation and DIAN validation
- PDF and XML download (base64-encoded)
- Email delivery of validated invoices
- Invoice event history (RADIAN)
- Reference data lookups (municipalities, taxes, units, numbering ranges, countries)
- Static DIAN reference tables in a single endpoint (no Factus token required)
- Acquirer lookup via DIAN — autocomplete customer data by document number
- Standardized `ApiResponse[T]` envelope on all responses

## Requirements

- Python 3.12+  (or Docker)
- A Factus account (sandbox or production)

## Setup

### Option A — Local (virtualenv)

```bash
# Clone and enter the project
git clone <repo-url>
cd factus-api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
```

### Option B — Docker Compose

```bash
cp .env.example .env   # fill in the values
docker compose up --build
```

The API is exposed on port `8000`.

### Environment variables (`.env`)

```env
# Factus API credentials
FACTUS_BASE_URL=https://api-sandbox.factus.com.co
FACTUS_CLIENT_ID=your_client_id
FACTUS_CLIENT_SECRET=your_client_secret

# JWT signing key (generate with: openssl rand -hex 32)
SECRET_KEY=your_random_secret_key

# "development" (enables /docs + /redoc) or "production" (disables them)
ENVIRONMENT=development

# Comma-separated list of allowed CORS origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

See `.env.example` for the full list of supported variables.

## Running the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs available at: `http://localhost:8000/api/v1/docs` (only when `ENVIRONMENT != production`).

## Running tests

```bash
pytest

# With coverage
pytest --cov=app.src --cov-report=html
```

## Architecture

```
app/
├── main.py                      # FastAPI app factory
├── api/
│   ├── deps.py                  # Shared dependencies (auth)
│   └── v1/
│       └── endpoints/
│           ├── auth.py          # Local + Factus auth (rate-limited)
│           ├── invoices.py      # Invoice CRUD
│           └── lookups.py       # Reference data
├── core/
│   ├── config.py                # Settings (pydantic-settings)
│   ├── limiter.py               # slowapi Limiter instance
│   ├── responses.py             # ApiResponse[T] wrapper
│   └── security.py              # JWT + password hashing
├── domain/
│   ├── exceptions.py            # FactusAPIError (structured gateway errors)
│   ├── models/                  # Pydantic domain models
│   └── interfaces/              # Abstract gateway contracts
└── infrastructure/
    └── gateways/                # Factus HTTP implementations
```

The architecture follows a ports-and-adapters pattern. Endpoints depend only on abstract interfaces; concrete Factus HTTP gateways are injected via FastAPI's `Depends()`.

## API Reference

All endpoints require two headers:

| Header | Value |
|---|---|
| `X-API-Key` | `<internal_api_key>` — clave compartida entre el backend de Baiji y este middleware |
| `X-Factus-Token` | `<factus_access_token>` — token OAuth2 obtenido mediante `/auth/factus/login` |

> **Autenticación servicio a servicio**: el middleware ya **no usa** un sistema de usuarios ni emite JWT locales. La autenticación se realiza exclusivamente mediante la `FACTUS_INTERNAL_API_KEY`, que debe coincidir en el `.env` de este servicio y en el de `backend-app-baiji`.

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/factus/login` | Autenticar contra Factus y obtener Factus Token |
| `POST` | `/api/v1/auth/factus/refresh` | Refrescar el Factus Token |

### Invoices

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/invoices/` | Create and validate an invoice (DIAN) |
| `GET` | `/api/v1/invoices/{number}` | Get invoice details |
| `GET` | `/api/v1/invoices/{number}/pdf` | Download PDF (base64) |
| `GET` | `/api/v1/invoices/{number}/xml` | Download XML (base64) |
| `GET` | `/api/v1/invoices/{number}/events` | Get RADIAN events |
| `POST` | `/api/v1/invoices/{number}/send-email` | Send invoice by email |
| `DELETE` | `/api/v1/invoices/reference/{code}` | Delete unvalidated invoice |

### Company (Empresa)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/company` | Get user company profile |
| `PUT` | `/api/v1/company` | Update user company profile |
| `POST` | `/api/v1/company/logo` | Update user company logo |

### Numbering Ranges (Rangos de Numeración)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/numbering-ranges` | List filtered numbering ranges |
| `POST` | `/api/v1/numbering-ranges` | Create a new numbering range |
| `GET` | `/api/v1/numbering-ranges/software` | List numbering ranges associated with software |
| `GET` | `/api/v1/numbering-ranges/{id}` | Get specific numbering range details |
| `PUT` | `/api/v1/numbering-ranges/{id}` | Update numbering range consecutive |
| `DELETE` | `/api/v1/numbering-ranges/{id}` | Delete numbering range |

### Lookups

All lookup endpoints require `Authorization: Bearer <local_jwt>`. Endpoints marked with * also require `X-Factus-Token`.

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/lookups/reference-tables` | JWT only | All fixed DIAN reference tables (see below) |
| `GET` | `/api/v1/lookups/municipalities` | JWT + Factus* | Colombian municipalities |
| `GET` | `/api/v1/lookups/taxes` | JWT + Factus* | Product tax types |
| `GET` | `/api/v1/lookups/units` | JWT + Factus* | Units of measure |
| `GET` | `/api/v1/lookups/countries?name=` | JWT + Factus* | Countries (optional name filter) |
| `GET` | `/api/v1/lookups/acquirer` | JWT + Factus* | Customer name + email from DIAN |

#### `/lookups/reference-tables`

Returns all fixed catalog tables defined by the DIAN in a single request. No Factus token needed — data is static and safe to cache on the frontend.

| Table key | Description |
|---|---|
| `identification_document_types` | IDs 1–11 (Cédula, NIT, Pasaporte, etc.) |
| `legal_organization_types` | Persona Jurídica / Persona Natural |
| `customer_tribute_types` | IVA / No aplica (with `id`, `code`, `name`) |
| `payment_methods` | Efectivo, Tarjeta, Transferencia, etc. |
| `payment_forms` | Pago de contado / Pago a crédito |
| `product_standard_codes` | UNSPSC, GTIN, Partida Arancelaria, etc. |
| `document_types` | 01 Factura electrónica / 03 Contingencia tipo 03 |

#### `/lookups/acquirer`

Queries the DIAN directly to retrieve the name and email of a customer by document type and number. Useful for auto-filling customer fields in an invoice form.

Query params: `identification_document_id` (int) and `identification_number` (string).

### Response envelope

All endpoints (except `POST /auth/login`) return:

```json
{
  "success": true,
  "message": "Factura creada exitosamente",
  "data": { ... },
  "errors": null
}
```

On error:

```json
{
  "detail": "Error al crear la factura: El campo id rango de numeración es inválido."
}
```

## Postman Collection

Import `factus_api_collection.json` to get a ready-to-use collection.

**Workflow:**

1. Run **Factus Login** — saves `factus_token` and `factus_refresh_token` automatically.
   - Requires `X-API-Key` header (configured in `FACTUS_INTERNAL_API_KEY` variable).
2. Run any **Invoices** or **Lookups** request.

The **Create Invoice** request generates a unique `reference_code` (timestamp-based) on every run via a pre-request script, preventing 409 duplicate conflicts. The returned `invoice_number` is automatically saved to `{{invoice_number}}` for use in subsequent requests (Get, PDF, XML, Email, Events).

## Sandbox credentials

| Field | Value |
|---|---|
| URL | `https://api-sandbox.factus.com.co` |
| Email | `sandbox@factus.com.co` |
| Password | `sandbox2024%` |
| Numbering range ID (Factura de Venta) | `8` (prefix `SETP`) |
| Internal API Key | `baiji-internal-secret-key-dev-2024-change-in-production` |
