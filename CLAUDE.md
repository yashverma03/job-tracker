# Job Tracker — Project Overview

A personal job-application tracker: a Django REST API backend backed by a database, and a React/TypeScript frontend that lists, filters, edits, and bulk-manages job applications (status, referral status, generated outreach messages, etc.).

This document is a high-level map for navigation only — architecture and folder layout, not implementation detail. It intentionally excludes anything that changes often (specific fields, statuses, endpoints, business rules).

## Repo Layout

```
job-tracker/
├── backend/     Django REST API
├── frontend/    React + TypeScript SPA (Vite)
└── README.md
```

## Backend (`backend/`) — Django REST Framework

Organized as a small modular monolith: shared infrastructure lives in `common/` and `config/`, feature code lives under `modules/<feature>/`.

```
backend/
├── config/            Django project setup — settings, root URL routing, ASGI/WSGI entrypoints
├── common/            Cross-cutting code shared by all modules
│   ├── exceptions/    API exception types + global exception handlers
│   ├── types/         Shared generic types (e.g. pagination)
│   └── utils/         Generic helpers (e.g. env access)
├── modules/
│   └── jobs/          The "jobs" feature module (current sole domain module)
│       ├── models/        Django ORM models (persistence layer)
│       ├── migrations/    Django schema migrations
│       ├── dto/            Request/response schemas + validation (DRF serializers)
│       ├── services/      Business logic, orchestrates models on behalf of views
│       ├── enums/         Domain enums (e.g. status enumerations)
│       ├── types/         Module-specific type definitions
│       ├── views.py       API views — thin, delegate to services
│       ├── urls.py        Module-level URL routes
│       └── apps.py        Django app config
├── manage.py
├── requirements.txt
└── docker-compose.yml     Local infra (e.g. database) for development
```

**Layering convention** (per module): `views` (HTTP in/out) → `dto` (validate/shape request & response payloads) → `services` (business logic) → `models` (persistence). New domain areas are expected to be added as sibling packages under `modules/`, following the same internal structure as `modules/jobs/`.

## Frontend (`frontend/`) — React + TypeScript (Vite)

Organized by feature module under `src/modules/`, with shared/reusable code under `src/common/`.

```
frontend/
├── public/                 Static assets
├── src/
│   ├── main.tsx             App entry point
│   ├── App.tsx              Root component / top-level composition
│   ├── index.css            Global styles
│   ├── common/              Shared, feature-agnostic code
│   │   ├── api/              API client(s) grouped by domain (e.g. jobs.service.ts)
│   │   ├── components/       Reusable, generic UI components (e.g. Dropdown)
│   │   ├── configs/           App-wide configuration (e.g. API base config)
│   │   ├── constants/         Shared constants (e.g. pagination defaults)
│   │   ├── hooks/              Shared React hooks
│   │   └── types/               Shared TypeScript types
│   └── modules/
│       └── jobs/            The "jobs" feature module (current sole domain module)
│           ├── components/      Feature UI: page, table, filters, modals, bulk actions, messaging
│           ├── hooks/            Feature-specific hooks (data fetching/mutations, React Query)
│           ├── constants/        Feature constants (status/referral option lists, profile data)
│           ├── interfaces/       Request/response shape definitions for the API
│           ├── types/            Feature-specific TypeScript types
│           └── utils/            Feature-specific helper functions (e.g. message/URL generation)
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig*.json
```

**Convention**: each feature lives under `src/modules/<feature>/` with its own `components/`, `hooks/`, `constants/`, `types/`/`interfaces/`, and `utils/` subfolders, mirroring the backend's per-module structure. Cross-feature/reusable code goes in `src/common/`. State/data-fetching is done via hooks that wrap the API layer (`common/api`), following a React Query–style pattern.

## Data Flow (end to end)

1. Frontend feature hook (`modules/jobs/hooks/`) calls a function in `common/api/jobs/`.
2. Request hits a Django `views.py` endpoint (routed via `modules/jobs/urls.py` → `config/urls.py`).
3. View validates/shapes the payload via a `dto/`, delegates business logic to `services/`.
4. Service reads/writes via `models/`, returns domain data.
5. View serializes the response via a response `dto/` and returns it.
6. Frontend hook updates local/query cache; feature components re-render.

## Where to Look

- **Add/change an API endpoint or business rule** → `backend/modules/jobs/{views.py, urls.py, services/, dto/}`
- **Add/change a persisted field** → `backend/modules/jobs/models/` + a new migration
- **Add/change a status/enum option** → `backend/modules/jobs/enums/` (backend) and `frontend/src/modules/jobs/constants/job.constants.ts` (frontend)
- **Add/change a UI element in the jobs table/filters/modals** → `frontend/src/modules/jobs/components/`
- **Add/change how data is fetched or mutated on the frontend** → `frontend/src/modules/jobs/hooks/`
- **Add a reusable UI primitive** → `frontend/src/common/components/`
- **Add a new feature area** (beyond "jobs")** → mirror the `modules/jobs/` structure on both backend and frontend

## Code Comments

Comments are the exception, not the default. Do not comment every line, obvious code, or simple statements.

Only add a comment when the code itself can't explain it — e.g. a non-obvious decision, a tricky edge case, a workaround, or a "why" that requires reasoning to figure out. If a reader could infer it from well-named code, skip the comment.

When a comment is warranted, keep it short (one line, to the point) and phrase it as part of the code's own explanation — never paste in task/prompt instructions or reference the current change ("added for X fix", "per user request").
