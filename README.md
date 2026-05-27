# Breathe ESG Carbon Accounting Prototype

A carbon accounting and ingestion prototype designed to process, normalize, and review multi-format corporate activity logs (SAP procurement, utility portal invoices, and Concur corporate travel records) to generate audit-ready greenhouse gas (GHG) emission reports.

---

## Architecture Overview

The system is designed as a monolithic platform comprising a Django backend (utilizing PostgreSQL) and a single-page React frontend.

```
                  ┌─────────────────────────────────┐
                  │          React SPA              │
                  │   Vite + Tailwind v4 + Query    │
                  └────────────────┬────────────────┘
                                   │
                           HTTP API requests
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │         Django Monolith         │
                  │   URL Routing (breathe_esg)     │
                  └────────────────┬────────────────┘
                                   │
                       Checks local vs token
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │    Access Control Middleware    │
                  │     IsAuthenticatedOrLocal      │
                  └────────────────┬────────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
         ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
         │apps.companies │ │apps.ingestion │ │apps.normaliz. │
         │Tenant boundary│ │Inbound pipeline│ │Unified records│
         └───────────────┘ └───────────────┘ └───────────────┘
```

---

## Directory Structure

*   [backend/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend) — Core Django project root.
    *   [breathe_esg/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/breathe_esg) — Settings, WSGI wrapper, and root URL routing.
        *   [settings.py](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/breathe_esg/settings.py) — PostgreSQL connections, installed apps, and REST framework configuration.
    *   [apps/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps) — Custom domain-specific modules.
        *   [companies/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/companies) — Defines the tenant boundary via the [Company](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/companies/models.py) model.
        *   [ingestion/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/ingestion) — Handles incoming raw files. Houses pipelines for SAP, Utility, and Travel.
        *   [normalization/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/normalization) — Holds unified emission metrics, review status, administrative events, and status transitions.
        *   [common/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/common) — Shared business logic, abstract validators, and local-testing permissions.
            *   [utils.py](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/common/utils.py) — Flexible date parsing, German decimal cleaning, and CSV column validations.
            *   [serializers.py](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/common/serializers.py) — [BaseIngestionSerializer](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/common/serializers.py) containing base file validation.
            *   [permissions.py](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/common/permissions.py) — Access control class [IsAuthenticatedOrLocal](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/common/permissions.py).
    *   [requirements.txt](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/requirements.txt) — Django dependencies.
*   [frontend/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend) — Single-page web application.
    *   [src/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src) — Components, page views, and API calls.
        *   [api.js](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/api.js) — Custom TanStack React Query mutations and queries interface.
        *   [App.jsx](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/App.jsx) — Layout and router tab states.
        *   [components/](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/components) — File upload utilities, tabular grids, and administrative trigger buttons.
*   [DECISIONS.md](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/DECISIONS.md) — Technical and architecture trade-offs.
*   [MODEL.md](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/MODEL.md) — Database schemas and relationship mappings.
*   [SOURCES.md](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/SOURCES.md) — Emission factors and calculation methodologies.
*   [TRADEOFFS.md](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/TRADEOFFS.md) — Product simplifications and scaling paths.

---

## Local Setup

### System Prerequisites
*   Python 3.10+
*   Node.js 18+
*   PostgreSQL database service

### 1. Backend Service Setup
1.  Navigate into the backend project root:
    ```bash
    cd backend
    ```
2.  Initialize and activate a virtual environment:
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install library dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Copy environment variables configurations:
    Create a `.env` file at the root level of the workspace (one level above `backend/`) based on the template:
    ```bash
    # Run from the parent workspace root:
    cp .env.example .env
    ```
    Ensure that the `DATABASE_URL` in `.env` points to an active PostgreSQL database.
5.  Execute database migrations:
    ```bash
    python manage.py migrate
    ```
6.  Start the development server:
    ```bash
    python manage.py runserver
    ```
    The API runs at `http://127.0.0.1:8000/`.

### 2. Frontend Application Setup
1.  Navigate into the frontend project directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Launch the Vite development server:
    ```bash
    npm run dev
    ```
    The application runs at `http://localhost:5173/`. Incoming `/api` requests are proxied directly to `http://127.0.0.1:8000` via [vite.config.js](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/vite.config.js).

---

## Access Control Layer

The platform enforces minimal production-ready permissions via the custom [IsAuthenticatedOrLocal](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/common/permissions.py) permission boundary:
*   **Local Testing**: Requests originating from localhost (`127.0.0.1` or `::1`) bypass credential requirements. This ensures the React application running locally communicates seamlessly with the API.
*   **Remote/Staging Deployment**: Any request arriving from non-localhost IPs requires standard user authentication (`request.user.is_authenticated`), protecting remote servers against public ingestion abuse and data scraping.

---

## API Contract

All endpoints expect `/api` prefix routing and consume/return JSON payloads unless specified as file uploads. A default company identifier (`00000000-0000-0000-0000-000000000001`) is integrated for prototype routing context.

| Endpoint Path | HTTP Method | Authentication Requirement | Input Parameters / Payload Schema | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/api/ingestion/sap-upload/` | `POST` | `IsAuthenticatedOrLocal` | **Multipart/Form-Data**<br>- `data_source_id` (UUID)<br>- `file` (CSV File) | Process German-formatted SAP material exports and convert them to Normalized Records. |
| `/api/ingestion/utility-upload/` | `POST` | `IsAuthenticatedOrLocal` | **Multipart/Form-Data**<br>- `data_source_id` (UUID)<br>- `file` (CSV File) | Process utility energy invoices. Triggers daily pro-rata splits across billing periods. |
| `/api/ingestion/travel-upload/` | `POST` | `IsAuthenticatedOrLocal` | **Multipart/Form-Data**<br>- `data_source_id` (UUID)<br>- `file` (CSV File) | Process Concur business travel logs. Performs flight-distance calculations. |
| `/api/review/records/` | `GET` | `IsAuthenticatedOrLocal` | **Query Parameter**<br>- `company_id` (UUID) | Retrieve all active normalized activity metrics for the specified tenant. |
| `/api/review/suspicious/` | `GET` | `IsAuthenticatedOrLocal` | **Query Parameter**<br>- `company_id` (UUID) | Retrieve records flagged as outliers or containing logical warnings. |
| `/api/review/audit/` | `GET` | `IsAuthenticatedOrLocal` | **Query Parameter**<br>- `company_id` (UUID) | Retrieve chronological administrative events and status transitions. |
| `/api/review/approve/` | `POST` | `IsAuthenticatedOrLocal` | **Query Parameter**: `company_id` (UUID)<br>**JSON Body**:<br>`{ "record_id": "UUID", "notes": "string" }` | Certify the record, moving state to `APPROVED`. |
| `/api/review/reject/` | `POST` | `IsAuthenticatedOrLocal` | **Query Parameter**: `company_id` (UUID)<br>**JSON Body**:<br>`{ "record_id": "UUID", "notes": "string" }` | Dispute the record back to source, moving state to `DISPUTED`. |
| `/api/review/lock/` | `POST` | `IsAuthenticatedOrLocal` | **Query Parameter**: `company_id` (UUID)<br>**JSON Body**:<br>`{ "record_id": "UUID", "notes": "string" }` | Freeze the record for audit. Sets `is_locked = True` and moves status to `LOCKED`. |

---

## Ingestion Details & Calculation Logic

1.  **SAP Procurement Pipeline**
    *   **Header Requirements**: `Materialbeleg`, `Buchungsdatum`, `Werk`, `Menge`, `Einheit`, `Materialtext`.
    *   **Conversions**: Maps German dates (`DD.MM.YYYY`) and parses numbers with German separators (e.g. dots for thousands, commas for decimals like `1.500,75` $\rightarrow$ `1500.75`).
    *   **Scope Calculations**: Resolves plant code matching against the [PlantLookup](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/backend/apps/ingestion/models.py) database table to attach geographic coordinates, and maps standard diesel or natural gas codes to hardcoded GHG emission factors.
2.  Utility Portal Pipeline
    *   **Header Requirements**: `meter_id`, `billing_period`, `consumption`, `unit`.
    *   **Calculations**: Converts raw consumption from MWh to kWh (if raw unit is MWh). If the billing period spans multiple calendar months, the pipeline splits the activity into daily pro-rata chunks, creating a dedicated [NormalizedRecord](file:///e:/WebDev/Intern%20Assignments/Breathe_ESG/backend/apps/normalization/models.py) row for each month to prevent analytical skewing.
3.  **Corporate Travel Pipeline**
    *   **Header Requirements**: `Category`, `Date`, `Origin`, `Destination`, `Distance`, `Unit`.
    *   **Calculations**: Segregates business travel into flights, hotels, or ground transport. Distances specified in units other than kilometers are automatically converted, and passenger flight footprints are computed via distance coefficients.

---

## Prototype Limitations & Roadmap

*   **Emission Factor Registry**: Calculations are based on fixed coefficients hardcoded in the codebase modules (see [SOURCES.md](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/SOURCES.md)). The production roadmap replaces this with a versioned relational `EmissionFactor` database.
*   **Authentication & Session Management**: Security is currently restricted to localhost checks via `IsAuthenticatedOrLocal`. Multi-tenant security in production must transition to JWT (JSON Web Tokens) or standard Session auth, replacing query parameter scoping.
*   **Job Batch Tracking**: Upload files are processed transactionally, generating direct database entries. A dedicated `Job` orchestration table will be needed to track large background worker loads.
