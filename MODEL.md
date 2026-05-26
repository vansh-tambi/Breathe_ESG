# Data Model Reference

Last updated: 2026-05-26
Author: engineering (prototype phase)

---

## Overview

Six core entities across three Django apps. The schema is deliberately flat — we avoided deep normalization because the prototype timeline (4 days) doesn't justify the complexity of a fully normalized star schema, and the query patterns we actually need are simple filtered scans, not analytical joins.

---

## Entity Map

```
Company
  │
  ├── DataSource (1:N)
  │     │
  │     └── RawRecord (1:N)
  │           │
  │           └── NormalizedRecord (1:1)
  │                 │
  │                 └── ReviewDecision (1:N, append-only)
  │
  └── PlantLookup (1:N, SAP-specific)
```

---

## Entities

### Company (`companies.Company`)

The tenant boundary. Every query in the system is scoped to a company. We use `PROTECT` on all foreign keys pointing here because deleting a company with existing emission data would be a compliance catastrophe.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | Auto-generated |
| name | CharField(255) | Display name |
| created_at | DateTimeField | auto_now_add — justified because onboarding timestamp matters for contract SLAs |

We considered adding `slug`, `industry_code`, `reporting_year` here. Deferred — the prototype doesn't need them and they'd be speculative.

---

### DataSource (`ingestion.DataSource`)

Represents a configured integration endpoint. Currently three types: `SAP_PROCUREMENT`, `UTILITY_PORTAL`, `TRAVEL_CONCUR`.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| company | FK → Company | PROTECT, indexed |
| name | CharField(255) | Human label, unique per company |
| source_type | CharField(50) | Choices enum |
| configuration_payload | JSONField | Stores column mappings, plant translation tables, API params. Intentionally schemaless — every client's SAP export has different column names |
| is_active | BooleanField | Soft toggle. We don't delete sources because raw records reference them |
| created_at, updated_at | DateTimeField | Justified: need to track when integrations were reconfigured |

**Why JSONField for config?** Because the alternative is a separate `DataSourceConfig` table with EAV pattern, which is worse in every way for this use case. The config is read once per upload, never queried against.

---

### RawRecord (`ingestion.RawRecord`)

Write-once storage of exactly what arrived in the CSV row. This is the compliance anchor — if an auditor asks "what did the source system actually say?", this is the answer.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| company | FK → Company | Denormalized from DataSource for query convenience. Yes, it's redundant. The alternative is a JOIN on every tenant-scoped query, which felt wrong for a table that could grow to millions of rows |
| data_source | FK → DataSource | PROTECT |
| job_id | UUID, indexed | Groups rows from one file upload. Not a FK to a Job table because we don't have a Job table — that's a simplification. A real system probably needs one |
| sequence_number | Integer | Line number in source file |
| raw_payload | JSONField | Exact key-value pairs from the CSV row |
| processing_state | CharField | UNPROCESSED → NORMALIZED or REJECTED |
| structural_error | TextField, nullable | Error message when state is REJECTED |
| created_at | DateTimeField | Legal arrival timestamp. No updated_at because this table is immutable — if you're tempted to update a raw record, something is architecturally wrong |

**Uncertainty:** We store `raw_payload` as JSON. For very large files (100k+ rows), this might cause storage bloat vs storing the original file as a blob. We chose per-row JSON because it makes line-level error reporting trivial. This might not be the right call at scale.

---

### PlantLookup (`ingestion.PlantLookup`)

SAP-specific mapping table. Translates SAP Werk (plant) codes to physical facility names and grid region codes. Only used by the SAP pipeline.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| company | FK → Company | |
| sap_plant_code | CharField(50) | e.g. "1000", "DE01" |
| facility_name | CharField(255) | Human-readable |
| grid_region_code | CharField(50) | Used for Scope 2 grid emission factor lookup |

**Why a separate table instead of putting this in DataSource.configuration_payload?** Because plant mappings are referenced per-row during processing, and we need indexed lookups on `(company, sap_plant_code)`. JSONField queries would be too slow.

---

### NormalizedRecord (`normalization.NormalizedRecord`)

The unified, carbon-calculated record. One NormalizedRecord per RawRecord (1:1). This is what analysts see in the Review UI.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| company | FK → Company | Again denormalized for query speed |
| raw_record | OneToOneField → RawRecord | SET_NULL — if a raw record is somehow removed, the normalized record survives as an orphan rather than cascading a delete |
| activity_type | CharField | FUEL_COMBUSTION, ELECTRICITY_CONSUMPTION, BUSINESS_TRAVEL |
| scope_classification | CharField | SCOPE_1, SCOPE_2, SCOPE_3 |
| reporting_date | DateField | The physical date of consumption, not the upload date |
| raw_quantity | Decimal(18,4) | Original numeric value before conversion |
| raw_unit | CharField(50) | Original unit string |
| normalized_quantity | Decimal(18,4) | After unit conversion (e.g. MWh → kWh) |
| normalized_unit | CharField(50) | Target unit |
| travel_category | CharField(20), nullable | flight/hotel/ground — only populated for BUSINESS_TRAVEL records |
| origin_airport_code | CharField(10), nullable | IATA code, travel-only |
| destination_airport_code | CharField(10), nullable | IATA code, travel-only |
| distance_km | Decimal(12,2), nullable | Travel distance in km |
| emission_factor_applied | Decimal(18,8) | The factor used. Stored explicitly so recalculations are traceable |
| co2e_metric_tons | Decimal(18,6) | Final carbon number |
| review_status | CharField | PENDING_REVIEW → SUSPICIOUS / APPROVED / DISPUTED / LOCKED |
| is_locked | BooleanField | Once true, record is immutable |
| created_at, updated_at | DateTimeField | Both justified: created_at for latency tracking, updated_at for review state transition auditing |

**Simplification:** The travel-specific fields (travel_category, airport codes, distance_km) are nullable columns on the same table rather than a separate `TravelDetail` model. This is a deliberate denormalization. For three optional fields, a separate table adds a JOIN cost with no real benefit. If we add 10+ travel-specific fields later, we should revisit.

**Simplification:** `emission_factor_applied` is a single decimal. In reality, emission factors have versions, sources (DEFRA vs EPA vs IPCC), and effective date ranges. We store just the number because building a proper EmissionFactor registry is a week of work by itself.

---

### ReviewDecision (`review.ReviewDecision`)

Append-only audit log. Every approve/reject/flag action creates a new row. Rows are never updated or deleted.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | |
| company | FK → Company | |
| normalized_record | FK → NormalizedRecord | PROTECT — can't delete a record that has audit history |
| analyst | FK → User, nullable | Currently always null in the prototype (no auth). In production this would be non-nullable |
| action_type | CharField | APPROVE, DISPUTE, FLAG_SUSPICIOUS |
| previous_state | CharField | What the record was before this action |
| new_state | CharField | What the record became |
| notes | TextField | Free-text justification |
| created_at | DateTimeField | No updated_at — this is an immutable log |

---

## Migration Sequence

1. `companies` — no dependencies
2. `ingestion` — depends on companies
3. `normalization` — depends on ingestion (RawRecord FK)
4. `review` — depends on normalization (NormalizedRecord FK)
5. `audit` — depends on review (future)

This ordering is strict. You cannot run normalization migrations before ingestion migrations exist.

---

## Known Gaps

- No `Job` or `UploadBatch` table — job_id is just a UUID on RawRecord. Means we can't store file-level metadata (filename, upload user, total row count) without querying aggregates.
- No `EmissionFactor` table — factors are hardcoded in pipeline functions. This is the single biggest technical debt item.
- No `User` model customization — using Django's default auth.User, which the prototype doesn't even require.
- `company` FK is denormalized onto RawRecord and NormalizedRecord. Correct but redundant. We accepted the storage cost for query simplicity.
