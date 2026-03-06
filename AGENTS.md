# Factus API - Agent Guidelines

This document provides guidelines for agents working on the Factus API project.

## Project Overview

FastAPI-based REST API for interacting with the Factus (Colombian e-invoicing) API. Uses clean architecture with domain-driven design patterns.

## Build, Lint, and Test Commands

### Running the Application

```bash
# Development server with auto-reload
uvicorn app.src.main:app --reload --host 0.0.0.0 --port 8000

# Or using fastapi CLI (if installed)
fastapi dev app/src/main.py
```

### Testing

The tests directory exists but is currently empty. When tests are added:

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Run a single test function
pytest tests/test_auth.py::test_login_success

# Run with coverage
pytest --cov=app.src --cov-report=html

# Run specific test by name pattern
pytest -k "test_login"
```

### Linting and Formatting

```bash
# Format code (Black + isort)
black app/
isort app/

# Lint code (Ruff)
ruff check app/

# Type checking (if mypy is added)
mypy app/
```

## Code Style Guidelines

### Project Structure

```
app/src/
├── main.py                 # FastAPI app factory
├── api/
│   ├── v1/
│   │   ├── endpoints/      # Route handlers
│   │   └── schemas/        # Pydantic request/response models
│   └── deps.py             # Dependency injection
├── core/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── security.py         # Password hashing, JWT
│   └── responses.py        # Custom response models
├── domain/
│   ├── models/             # Domain entities
│   └── interfaces/         # Abstract interfaces (ports)
└── infrastructure/
    ├── gateways/           # External API implementations
    ├── repositories/       # Database implementations
    └── db/                 # Database setup
```

### Import Conventions

- Use absolute imports: `from app.src.module import ...`
- Order: stdlib → third-party → local
- Use `isort` for automatic sorting

```python
# Correct
import asyncio
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.src.api.deps import get_current_user
from app.src.core.config import settings
from app.src.domain.models.user import User
```

### Type Annotations

- Always use type hints for function arguments and return values
- Use `Optional[T]` instead of `T | None`
- Use concrete types when possible (e.g., `list[str]` over `List[str]`)

```python
# Correct
def process_data(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

async def fetch_data(url: str, timeout: int = 30) -> Optional[dict]:
    ...

# Avoid
def process_data(items):
    return {item: len(item) for item in items}
```

### Naming Conventions

- **Variables/Functions**: `snake_case` (e.g., `get_user_by_id`, `user_data`)
- **Classes**: `PascalCase` (e.g., `FactusAuthGateway`, `UserInDB`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Files**: `snake_case.py` (e.g., `auth_gateway.py`, `user_model.py`)
- **Routes**: Use descriptive plural nouns (e.g., `/invoices`, `/lookups`)

### Pydantic Models

- Use `BaseModel` for request/response schemas
- Use explicit types with `Field()` for validation
- Use `EmailStr` for email fields
- Use `Optional[T]` with default `None` for optional fields

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
```

### Error Handling

- Use HTTPException for HTTP errors with appropriate status codes
- Return meaningful error messages in Spanish (project language)
- Catch specific exceptions, avoid bare `except:`

```python
# Correct
try:
    result = await gateway.fetch_data()
except httpx.HTTPStatusError as e:
    raise HTTPException(
        status_code=400,
        detail=f"Error al obtener datos de Factus: {str(e)}"
    )

# Avoid
try:
    result = await gateway.fetch_data()
except Exception:
    pass
```

### Async/Await

- Use `async def` for route handlers and gateway methods
- Always `await` async functions
- Use `httpx.AsyncClient` for HTTP requests (never `requests`)

```python
# Correct
@router.get("/items/{item_id}")
async def get_item(item_id: str) -> Item:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/items/{item_id}")
        return Item(**response.json())

# Avoid
@router.get("/items/{item_id}")
def get_item(item_id: str) -> Item:
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    return Item(**response.json())
```

### Dependency Injection

- Use FastAPI's `Depends()` for dependency injection
- Create factory functions for gateway/infrastructure initialization
- Use `app/src/api/deps.py` for shared dependencies

```python
def get_auth_gateway() -> FactusAuthGateway:
    return FactusAuthGateway(
        base_url=settings.FACTUS_BASE_URL,
        client_id=settings.FACTUS_CLIENT_ID,
        client_secret=settings.FACTUS_CLIENT_SECRET
    )

@router.post("/login")
async def login(gateway: FactusAuthGateway = Depends(get_auth_gateway)):
    ...
```

### Configuration

- Use `pydantic-settings` for settings management
- Define defaults in `core/config.py`
- Load from `.env` file (already in `.gitignore`)
- Never hardcode secrets

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Factus API"
    FACTUS_BASE_URL: str
    SECRET_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### HTTP Clients

- Use `httpx.AsyncClient` for all HTTP calls
- Always use context manager: `async with httpx.AsyncClient() as client:`
- Check `response.is_success` before processing
- Call `response.raise_for_status()` on errors

```python
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=payload)
    
    if not response.is_success:
        response.raise_for_status()
    
    return response.json()
```

### Comments and Documentation

- Avoid comments unless explaining business logic
- Use docstrings for complex functions
- Keep code self-documenting with clear naming

### Security

- Never log or expose secrets
- Use environment variables for all credentials
- Hash passwords with bcrypt (already configured)
- Validate all input with Pydantic models

## Running Single Tests

To run a specific test:

```bash
# By file
pytest tests/test_auth.py

# By function
pytest tests/test_auth.py::test_login_success

# By marker
pytest -m "unit"

# By keyword
pytest -k "auth"
```

## Common Issues

- **Import errors**: Ensure you're in the project root and `app/` is importable
- **Environment variables**: Copy `.env` from `.env.example` or template
- **httpx errors**: Always check response status before accessing `.json()`
