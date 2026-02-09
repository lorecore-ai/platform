# Modules

Application business logic is organized under `app/modules/`. Each module encapsulates its own area of responsibility.

## Module structure

Typical components:

- **`models.py`** — data models (DB, domain entities).
- **`schemas.py`** — Pydantic schemas for the API (if the module has a router).
- **`service.py`** — core business logic (service layer).
- **`router.py`** — FastAPI HTTP endpoints (if the module exposes an API).
- **`deps.py`** — dependencies for injection into routers and services.

## Platform modules

| Module | Purpose |
|--------|---------|
| **events** | Events from integrations and internal events; storage and processing. |
| **integrations** | Registering integrations in the DB, configuration, syncing with the connector registry. |
| **secrets** | Access to secrets (e.g. via Vault) for integrations and services. |
| **tenants** | Multi-tenancy: tenants, data isolation per tenant. |

Modules use shared dependencies: the database (`app.core.database`), the integration registry, and the secrets manager. These are initialized at application startup and passed into services via `deps` or `app.state`.
