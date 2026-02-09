# LoreCore

## Quick start

1. Go to the infra directory and start the stack with Docker Compose:

   ```bash
   cd infra/docker
   docker compose up -d --build
   ```

2. The API will be available at `http://localhost:8000`. Postgres, Vault, backend and docs run in containers. Technical documentation (MkDocs) — at `http://localhost:8080/`.