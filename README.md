# Factus API

REST API built with FastAPI that acts as a secure intermediary for the [Factus](https://factus.com.co) Colombian e-invoicing platform. It exposes authenticated endpoints for creating, querying, downloading, and managing electronic invoices validated by the DIAN.

## Features

- JWT-based local authentication
- Full Factus OAuth2 token lifecycle (login + refresh)
- Invoice creation and DIAN validation
- PDF and XML download (base64-encoded)
- Email delivery of validated invoices
- Invoice event history (RADIAN)
- Reference data lookups (municipalities, taxes, units, numbering ranges)
- Standardized `ApiResponse[T]` envelope on all responses

## Requirements

- Python 3.12+
- A Factus account (sandbox or production)

## Setup

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

### Environment variables (`.env`)

```env
FACTUS_BASE_URL=https://api-sandbox.factus.com.co
FACTUS_CLIENT_ID=your_client_id
FACTUS_CLIENT_SECRET=your_client_secret
SECRET_KEY=your_random_secret_key
```

## Running the server

```bash
uvicorn app.src.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs available at: `http://localhost:8000/api/v1/docs`

## Running tests

```bash
pytest

# With coverage
pytest --cov=app.src --cov-report=html
```

## Architecture

```
app/src/
├── main.py                      # FastAPI app factory
├── api/
│   ├── deps.py                  # Shared dependencies (auth)
│   └── v1/
│       └── endpoints/
│           ├── auth.py          # Local + Factus auth
│           ├── invoices.py      # Invoice CRUD
│           └── lookups.py       # Reference data
├── core/
│   ├── config.py                # Settings (pydantic-settings)
│   ├── responses.py             # ApiResponse[T] wrapper
│   └── security.py              # JWT + password hashing
├── domain/
│   ├── models/                  # Pydantic domain models
│   └── interfaces/              # Abstract gateway contracts
└── infrastructure/
    └── gateways/                # Factus HTTP implementations
```

The architecture follows a ports-and-adapters pattern. Endpoints depend only on abstract interfaces; concrete Factus HTTP gateways are injected via FastAPI's `Depends()`.

## API Reference

All protected endpoints require two headers:

| Header | Value |
|---|---|
| `Authorization` | `Bearer <local_jwt>` |
| `X-Factus-Token` | `<factus_access_token>` |

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Local login — returns local JWT |
| `POST` | `/api/v1/auth/factus/login` | Authenticate against Factus |
| `POST` | `/api/v1/auth/factus/refresh` | Refresh Factus access token |

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

### Lookups

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/lookups/numbering-ranges` | Available numbering ranges |
| `GET` | `/api/v1/lookups/municipalities` | Colombian municipalities |
| `GET` | `/api/v1/lookups/taxes` | Product tax types |
| `GET` | `/api/v1/lookups/units` | Units of measure |

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

1. Run **1. Local Login** — saves `local_jwt` automatically.
2. Run **2. Factus Login** — saves `factus_token` and `factus_refresh_token` automatically.
3. Run any **Invoices** or **Lookups** request.

The **Create Invoice** request generates a unique `reference_code` (timestamp-based) on every run via a pre-request script, preventing 409 duplicate conflicts. The returned `invoice_number` is automatically saved to `{{invoice_number}}` for use in subsequent requests (Get, PDF, XML, Email, Events).

## Sandbox credentials

| Field | Value |
|---|---|
| URL | `https://api-sandbox.factus.com.co` |
| Email | `sandbox@factus.com.co` |
| Password | `sandbox2024%` |
| Numbering range ID (Factura de Venta) | `8` (prefix `SETP`) |

Local mock user: `admin` / `admin123`
