# Table-Order Backend (U1 backend-core)

Multi-tenant table-order service — FastAPI modular monolith.
This unit (backend-core) provides cross-cutting infrastructure (`app/core`) and shared
domain models (`app/shared`). Domain modules (auth/menu/order) are added in later units.

## Structure
```
backend/
  app/
    core/       # config, db, context, middleware, logging, errors, notifier,
                # ratelimit, events, health, metrics
    shared/     # SQLAlchemy models, TenantScopedRepository, common schemas
    main.py     # FastAPI app factory
  alembic/      # migrations
  tests/        # unit + property-based (Hypothesis) tests
  scripts/      # backup.sh
```

## Local run (docker-compose)
```bash
cp backend/.env.example backend/.env   # then edit secrets
docker compose up -d --build
# backend: http://localhost:8000  (docs: /docs, health: /health)
```

## Run tests
```bash
cd backend
pip install -e ".[dev]"
pytest
```

## Migrations
```bash
cd backend
alembic upgrade head        # apply
alembic downgrade -1        # rollback one revision  [RES-04]
```

## Extensions
- Security Baseline, Property-Based Testing (Hypothesis), Resiliency Baseline — enforced.
- Prod note: enforce HTTPS/HSTS in front of the app (local runs over HTTP). [SEC-04]
