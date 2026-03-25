# Factus API

REST API built with FastAPI that acts as a secure intermediary for the [Factus](https://factus.com.co) Colombian e-invoicing platform. It exposes authenticated endpoints for creating, querying, downloading, and managing electronic invoices validated by the DIAN.

## Features

- JWT-based local authentication
- Full Factus OAuth2 token lifecycle (login + refresh)
- Company profile management (view, update, logo update)
- Numbering Ranges management (CRUD operations)
- Invoice creation and DIAN validation
- Credit Note creation and DIAN validation
- PDF and XML download (base64-encoded) for invoices and credit notes
- Email delivery of validated documents
- Filtering and querying capabilities
- Invoice event history (RADIAN) and implicit acceptance
- Reference data lookups (municipalities, taxes, units, numbering ranges, countries)
- Static DIAN reference tables in a single endpoint (no Factus token required)
- Acquirer lookup via DIAN — autocomplete customer data by document number

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

```text
app/
├── main.py                      # FastAPI app factory
├── api/
│   ├── deps.py                  # Dependency injection + service factories
│   └── v1/
│       └── routers/
│           ├── auth.py          # Local + Factus auth (rate-limited)
│           ├── company.py       # Company profile management
│           ├── invoices.py      # Invoice CRUD
│           ├── lookups.py       # Reference data
│           └── numbering_ranges.py  # Numbering ranges CRUD
├── core/
│   ├── config.py                # Settings (pydantic-settings)
│   ├── exceptions.py            # FactusAPIError (structured API errors)
│   └── limiter.py               # slowapi Limiter instance
├── schemas/                     # Pydantic request/response models
└── services/
    ├── interfaces.py            # Generic service Protocols (provider-agnostic)
    └── providers/
        └── factus/              # Factus-specific implementations
            ├── factus_auth_service.py
            ├── factus_code_maps.py
            ├── factus_company_service.py
            ├── factus_document_service.py
            ├── factus_invoice_service.py
            ├── factus_credit_note_service.py
            ├── factus_lookup_service.py
            └── factus_numbering_range_service.py
```

The architecture follows a **Service Layer + Provider Adapter** pattern. Routers depend only on generic `Protocol` interfaces defined in `services/interfaces.py`. Concrete Factus implementations live in `services/providers/factus/`. The `api/deps.py` is the single factory that wires interfaces to implementations via FastAPI's `Depends()`.

## API Reference

All endpoints require two headers:

| Header | Value |
|---|---|
| `X-API-Key` | `<internal_api_key>` — Shared key between Baiji backend and this middleware |
| `X-Factus-Token` | `<factus_access_token>` — OAuth2 token obtained via `/auth/factus/login` |

> **Service-to-service authentication**: The middleware **no longer uses** a user system or issues local JWTs. Authentication is performed exclusively via the `FACTUS_INTERNAL_API_KEY`, which must match in the `.env` of this service and in `backend-app-baiji`.

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/factus/login` | Authenticate against Factus and obtain Factus Token |
| `POST` | `/api/v1/auth/factus/refresh` | Refresh the Factus Token |

### Invoices

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/invoices/` | Create and validate an invoice (DIAN) |
| `GET` | `/api/v1/invoices/` | List and filter invoices |
| `GET` | `/api/v1/invoices/{number}` | Get invoice details |
| `GET` | `/api/v1/invoices/{number}/pdf` | Download PDF (base64) |
| `GET` | `/api/v1/invoices/{number}/xml` | Download XML (base64) |
| `GET` | `/api/v1/invoices/{number}/events` | Get RADIAN events |
| `GET` | `/api/v1/invoices/{number}/email-content` | Get email delivery content for invoice |
| `POST` | `/api/v1/invoices/{number}/send-email` | Send invoice by email |
| `POST` | `/api/v1/invoices/{number}/implicit-acceptance` | Register implicit acceptance |
| `DELETE` | `/api/v1/invoices/reference/{code}` | Delete unvalidated invoice |

### Credit Notes

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/credit-notes/` | Create and validate a credit note (DIAN) |
| `GET` | `/api/v1/credit-notes/` | List and filter credit notes |
| `GET` | `/api/v1/credit-notes/{number}` | Get credit note details |
| `GET` | `/api/v1/credit-notes/{number}/pdf` | Download PDF (base64) |
| `GET` | `/api/v1/credit-notes/{number}/xml` | Download XML (base64) |
| `GET` | `/api/v1/credit-notes/{number}/email-content` | Get email delivery content for credit note |
| `POST` | `/api/v1/credit-notes/{number}/send-email` | Send credit note by email |
| `DELETE` | `/api/v1/credit-notes/reference/{code}` | Delete unvalidated credit note |

### Company Profile

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/company` | Get user company profile |
| `PUT` | `/api/v1/company` | Update user company profile |
| `POST` | `/api/v1/company/logo` | Update user company logo |

### Numbering Ranges

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/numbering-ranges` | List filtered numbering ranges |
| `POST` | `/api/v1/numbering-ranges` | Create a new numbering range |
| `GET` | `/api/v1/numbering-ranges/software` | List numbering ranges associated with software |
| `GET` | `/api/v1/numbering-ranges/{id}` | Get specific numbering range details |
| `PUT` | `/api/v1/numbering-ranges/{id}` | Update numbering range consecutive |
| `DELETE` | `/api/v1/numbering-ranges/{id}` | Delete numbering range |

### Lookups

All lookup endpoints require `X-API-Key`. Endpoints marked with * also require `X-Factus-Token`.

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/lookups/reference-tables` | API Key only | All fixed DIAN reference tables (see below) |
| `GET` | `/api/v1/lookups/municipalities` | API Key + Factus* | Colombian municipalities |
| `GET` | `/api/v1/lookups/taxes` | API Key + Factus* | Product tax types |
| `GET` | `/api/v1/lookups/units` | API Key + Factus* | Units of measure |
| `GET` | `/api/v1/lookups/countries?name=` | API Key + Factus* | Countries (optional name filter) |
| `GET` | `/api/v1/lookups/acquirer` | API Key + Factus* | Customer name + email from DIAN |

#### `/lookups/reference-tables`

Returns all fixed catalog tables defined by the DIAN in a single request. No Factus token needed — data is static and safe to cache on the frontend.

| Table key | Description |
|---|---|
| `identification_document_types` | IDs 1–11 (National ID, NIT, Passport, etc.) |
| `legal_organization_types` | Legal Entity / Natural Person |
| `customer_tribute_types` | VAT / Not applicable (with `id`, `code`, `name`) |
| `payment_methods` | Cash, Credit Card, Bank Transfer, etc. |
| `payment_forms` | Cash Payment / Credit Payment |
| `product_standard_codes` | UNSPSC, GTIN, Tariff Heading, etc. |
| `document_types` | 01 Electronic Invoice / 03 Contingency type 03 |

#### `/lookups/acquirer`

Queries the DIAN directly to retrieve the name and email of a customer by document type and number. Useful for auto-filling customer fields in an invoice form.

Query params: `identification_document_type` (string, e.g. `CC`, `NIT`, `TI`) and `identification_number` (string). `factus-api` maps the canonical code to the Factus integer ID internally.

### Response format

All endpoints (except `POST /auth/login`) return the raw JSON model directly. For example, creating an invoice or credit note returns a `DocumentResult`:

```json
{
  "number": "SETP990000001",
  "prefix": "SETP",
  "cufe": "551ad63b123...",
  "qr_url": "https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=...",
  "status": "1",
  "message": "Success"
}
```

On error:

```json
{
  "detail": "Error creating invoice: The numbering range id field is invalid."
}
```

## Postman Collection

Import `factus_api_collection.json` to get a ready-to-use collection.

**Workflow:**

1. Run **Factus Login** — saves `factus_token` and `factus_refresh_token` automatically.
   - Requires `X-API-Key` header (configured in `FACTUS_INTERNAL_API_KEY` variable).
2. Run any **Invoices**, **Credit Notes**, or **Lookups** request.

The **Create Invoice** and **Create Credit Note** requests generate unique `reference_code` (timestamp-based) on every run via a pre-request script, preventing duplicate conflicts. The returned `number` is automatically saved to `{{invoice_number}}` or `{{credit_note_number}}` for use in subsequent requests (Get, PDF, XML, Email, Events).

## Sandbox credentials

| Field | Value |
|---|---|
| URL | `https://api-sandbox.factus.com.co` |
| Email | `sandbox@factus.com.co` |
| Password | `sandbox2024%` |
| Numbering range ID (Factura de Venta) | `8` (prefix `SETP`) |
| Internal API Key | `baiji-internal-secret-key-dev-2024-change-in-production` |
