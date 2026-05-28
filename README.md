# Breathe ESG Carbon Accounting Prototype

This repository contains the prototype implementation for the Breathe ESG internship assignment. The project is designed to process, normalize, and review multi-format corporate activity logs (SAP procurement files, utility invoices, and Concur travel logs) to generate unified greenhouse gas (GHG) emission records.

## Deployment Links

* Frontend: https://breathe-esg-flame-theta.vercel.app
* Backend API: https://breatheesg-production-c0df.up.railway.app
* Portfolio: https://vanshtambi.in/

## Project Overview

The prototype solves a core data engineering challenge in carbon accounting: taking raw, unstructured, or differently structured corporate data from various departments, validating it, converting it to standard units (e.g., Liters, kWh, kilometers), and calculating CO2 equivalents (CO2e) based on established emission factors.

It features:
* An ingestion pipeline that processes file uploads and handles row-level parsing and validation.
* Database models that separate immutable raw input records from auditable normalized output records.
* A React dashboard that allows sustainability analysts to review, approve, dispute, or lock records for compliance audits.

## Tech Stack

* Frontend: React (Vite, vanilla CSS for layout, and TanStack React Query for state and cache management).
* Backend: Django and Django REST Framework.
* Database: PostgreSQL (configured with sslmode require in production).
* Deployment: Railway for backend and database services, Vercel for frontend hosting.

## Architecture Overview

The backend uses a structured application layout where responsibilities are separated into distinct Django apps:

* apps/companies: Enforces the tenant boundary. All ingestion data, raw records, and normalized outputs are partitioned by Company ID.
* apps/ingestion: Handles file ingestion, parsing logic, and schema validation for the different pipelines.
* apps/normalization: Manages normalized emissions records, analyst review statuses, and the audit trail of review decisions.
* apps/common: Shares utility functions (e.g., date parsing, decimal sanitization, and CSV column validation) and local-development access control rules.

## Project Structure

```
.
├── backend/
│   ├── apps/
│   │   ├── companies/       # Tenant partitioning logic
│   │   ├── ingestion/       # CSV pipelines (SAP, Utility, Travel)
│   │   ├── normalization/   # Normalized GHG metrics and review states
│   │   └── common/          # Shared utilities and helper serializers
│   ├── breathe_esg/         # Main settings and routing configurations
│   ├── manage.py            # Django administrative entrypoint
│   └── requirements.txt     # Backend python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (Upload modal, Review grids)
│   │   ├── pages/           # Page layouts (Data Ingestion, Review Board)
│   │   ├── api.js           # API request layer using React Query
│   │   └── App.jsx          # Main application layout and routing
│   ├── package.json         # Frontend node dependencies
│   └── vite.config.js       # Vite build configurations with dev proxy
├── DECISIONS.md             # Technical and structural design decisions
├── MODEL.md                 # Database schema definitions and relationships
├── SOURCES.md               # Scientific sources for emission factors
└── TRADEOFFS.md            # Product tradeoffs and scaling notes
```

## CSV Ingestion Workflow

The ingestion pipeline handles three specific upload formats:

1. SAP Procurement Logs
   * Required columns: Materialbeleg, Buchungsdatum, Werk, Menge, Einheit, Materialtext.
   * Processes German localization formats, cleaning decimal separators (dots for thousands, commas for decimals) and converting dates.
   * Automatically maps SAP plant codes (Werk) to facilities and calculates diesel or natural gas combustions. If a plant code is missing in the database lookups, it auto-creates it on the fly with a demo fallback to avoid failing the upload.

2. Utility Portal Invoices
   * Required columns: meter_id, billing_period, consumption, unit.
   * Converts MWh to kWh consumption metrics.
   * Dynamically splits energy consumption across months. If an invoice spans multiple calendar months, the pipeline calculates the daily rate and creates pro-rata normalized slices per month to prevent analytical distortion.

3. Corporate Travel Records
   * Required columns: Category, Date, Origin, Destination, Distance, Unit.
   * Segregates travel emissions by type (flight, hotel, ground transport).
   * Standardizes distances to kilometers and resolves flight passenger footprint coefficients.

## Validation & Error Handling

To support real-world corporate file uploads, the backend implements robust validation and partial ingestion mechanisms:

* Partial Ingestion Support: Processing loops run inside a single transaction but handle individual row parsing inside try-except blocks. If a row is corrupted or invalid, it is caught, logged, and saved as REJECTED with a detailed error log, while all valid rows continue to ingest and commit as NORMALIZED.
* Row-Level Validation Errors: Row failures do not reject the entire file. The response payload returns a detailed JSON summary showing exactly which lines failed and why, which is then rendered on the frontend dashboard to help developers and analysts debug source logs.

## Review and Audit Workflow

Once raw logs are ingested and normalized, they enter the analyst review board:

* Suspicious Record Detection: Records containing mathematical outliers or logical warnings (such as a negative value or anomalous quantity) are automatically flagged as SUSPICIOUS and surfaced in a dedicated review tab for the analyst.
* Approval/Rejection Flow: Analysts can select records to certify (moves state to APPROVED) or dispute back to the source team (moves state to DISPUTED). Notes are required for these actions.
* Compliance Locking: Approved records can be locked (moves state to LOCKED). This locks the record against any subsequent modifications or recalculations to ensure data integrity for external audit.
* Audit Log: All state transitions (ingest, flag, approve, dispute, lock) are permanently written to an administrative audit event ledger.

## Local Setup Instructions

### Prerequisites
* Python 3.10+
* Node.js 18+
* PostgreSQL service running locally or remotely

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Initialize and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```
   The backend API will run at http://127.0.0.1:8000/.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend application will run at http://localhost:5173/. Vite is configured to proxy all `/api/*` requests to the local Django port.

## Environment Variables

Create a `.env` file at the root of the project (one level above `backend/`) based on the `.env.example` file:

```env
DEBUG=True
SECRET_KEY=local-dev-secret-key-change-in-production
DATABASE_URL=postgres://username:password@localhost:5432/breathe_esg_db
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/ingestion/sap-upload/` | Upload and process SAP material procurement CSV files |
| `POST` | `/api/ingestion/utility-upload/` | Upload and process utility energy invoices |
| `POST` | `/api/ingestion/travel-upload/` | Upload and process corporate travel logs |
| `GET` | `/api/review/records/` | Retrieve normalized activity records (filtered by company_id) |
| `GET` | `/api/review/suspicious/` | Retrieve records flagged as suspicious |
| `GET` | `/api/review/audit/` | Retrieve the chronological audit trail |
| `POST` | `/api/review/approve/` | Approve a record (Transition to APPROVED) |
| `POST` | `/api/review/reject/` | Reject/dispute a record (Transition to DISPUTED) |
| `POST` | `/api/review/lock/` | Lock a record for auditing (Transition to LOCKED) |

## Future Improvements

* Emission Factor Database: Move emissions factors from local static dictionaries to a versioned database table to support dynamic policy updates.
* JWT/Session Auth: Integrate a proper token-based login flow for multi-tenant isolation, replacing the current local-bypass permissions.
* Async Task Processing: Move parsing and normalization for massive CSV uploads to background task queues using Celery or Redis.
