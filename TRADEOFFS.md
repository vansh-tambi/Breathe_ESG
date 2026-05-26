# Tradeoffs Register

Last updated: 2026-05-26
Author: engineering (prototype phase)

This document lists the tradeoffs we knowingly made, what we gained, what we lost, and when each one becomes a problem.

---

## T1: Synchronous Processing vs Background Jobs

| | |
|---|---|
| **What we chose** | Process CSV uploads synchronously inside the HTTP request |
| **What we gained** | No Celery/Redis dependency, no task status polling, simpler error handling, immediate response with results |
| **What we lost** | Ability to handle large files (50k+ rows), ability to show progress indicators, ability to retry partial failures |
| **When it breaks** | When someone uploads a 100k-row SAP export and the request times out at 30 seconds |
| **Effort to fix** | 2-3 days: add Celery, create Job model, build status-polling endpoint, update frontend to show progress |

---

## T2: Hardcoded Emission Factors vs Factor Database

| | |
|---|---|
| **What we chose** | Emission factors as Python constants in pipeline modules |
| **What we gained** | Immediate functionality, no schema design for factor versioning, no admin UI for factor management |
| **What we lost** | Ability to update factors without code deployment, ability to track which factor version was applied, ability to support multiple factor databases (DEFRA, EPA, IPCC), regional/temporal factor variants |
| **When it breaks** | As soon as anyone asks "can we use the 2024 DEFRA factors instead?" or "which factor version was used for Q3 2025 reporting?" |
| **Effort to fix** | 5-7 days: EmissionFactor model with (source, category, region, year, value) fields, admin interface, factor selection logic in pipelines, migration of existing hardcoded values |
| **Honest note** | The hotel/ground travel factor (0.05 kg CO₂e/km) is fabricated. It's not from any published methodology. It prevents the pipeline from crashing on non-flight rows. That's it. |

---

## T3: Per-Row JSON Storage vs File Blob Storage

| | |
|---|---|
| **What we chose** | Store each CSV row as a JSON object in RawRecord.raw_payload |
| **What we gained** | Line-level error reporting, ability to query individual fields within raw data, no need to re-parse files |
| **What we lost** | Storage efficiency. A 5000-row CSV stored as 5000 JSON objects with repeated key names uses 3-5x more space than the original file |
| **When it breaks** | At high ingest volumes. 1M raw records × 500 bytes average JSON = ~500MB just for raw_payload. Manageable but not free |
| **Effort to fix** | Not clear this needs fixing. Could compress old raw records into cold storage if needed. Could also store original file as blob alongside per-row JSON and garbage-collect the JSON after processing |

---

## T4: Flat NormalizedRecord vs Type-Specific Tables

| | |
|---|---|
| **What we chose** | Single NormalizedRecord table with nullable travel-specific fields |
| **What we gained** | One table to query for all emission records regardless of type, simple API serializers, no polymorphic query complexity |
| **What we lost** | Schema purity. Travel fields (travel_category, airport codes, distance_km) are null for 100% of fuel combustion and electricity records. That's wasted nullable columns |
| **When it breaks** | If we add 10+ type-specific fields per activity type. Then the table has 30+ nullable columns and the schema becomes confusing |
| **Effort to fix** | Medium: create FuelCombustionDetail, ElectricityDetail, TravelDetail tables with 1:1 FK to NormalizedRecord. Migrate existing data. Update serializers to include nested detail |

---

## T5: No Authentication vs Production Auth

| | |
|---|---|
| **What we chose** | AllowAny permissions, company_id as query parameter |
| **What we gained** | Zero time spent on auth infrastructure. Can demo any tenant's data instantly |
| **What we lost** | Any form of access control. Anyone with the URL can read, modify, or lock any tenant's data. No audit trail of who performed review actions |
| **When it breaks** | Immediately upon any non-localhost deployment |
| **Effort to fix** | 1-2 days: SimpleJWT integration, user-tenant mapping, replace query param with token-derived tenant, add analyst FK to ReviewDecision |

---

## T6: Denormalized company FK vs Normalized Joins

| | |
|---|---|
| **What we chose** | company FK on RawRecord, NormalizedRecord, ReviewDecision (redundant with DataSource chain) |
| **What we gained** | Single-index tenant-scoped queries without JOINs |
| **What we lost** | Data redundancy, risk of FK staleness if tenant ownership changes |
| **When it breaks** | If we need to migrate data between tenants (unlikely but possible in multi-tenant SaaS) |
| **Effort to fix** | Low: write a management command that re-derives company from the DataSource chain and updates denormalized FKs |

---

## T7: React Query Only vs Redux

| | |
|---|---|
| **What we chose** | React Query for all state management, no Redux/Context |
| **What we gained** | Less boilerplate, automatic cache invalidation, no manual store synchronization |
| **What we lost** | No client-side state management for complex UI flows (filters, selections, undo). All state resets on navigation |
| **When it breaks** | If we add complex filter combinations, multi-step wizards, or undo functionality. React Query manages server cache, not UI state |
| **Effort to fix** | Could add Zustand (lightweight) or Context for specific UI state needs without replacing React Query. They compose well together |

---

## T8: Even Pro-Rata Distribution vs Actual Load Profiles

| | |
|---|---|
| **What we chose** | Split multi-month utility bills evenly across days |
| **What we gained** | Deterministic, reproducible allocation that's easy to explain to auditors |
| **What we lost** | Accuracy. A factory that runs 24/7 in winter and shuts down in summer will have wildly uneven consumption. Even distribution masks this |
| **When it breaks** | When monthly emission reports show suspiciously smooth curves that don't match operational reality |
| **Effort to fix** | Medium-high: need operational calendars, degree-day data, or actual sub-metered readings. The even-distribution approach is standard practice in many ESG frameworks, so this might actually be "correct enough" for reporting purposes |

---

## T9: German-Only Header Parsing vs Configurable Headers

| | |
|---|---|
| **What we chose** | Hardcoded German column names in the SAP pipeline (Buchungsdatum, Menge, Einheit, etc.) |
| **What we gained** | Immediate working pipeline for the specific SAP export format we were given |
| **What we lost** | Flexibility. An SAP system configured for English or French headers will fail validation immediately |
| **When it breaks** | When onboarding a non-German SAP client |
| **Effort to fix** | Low-medium: move header mappings into DataSource.configuration_payload. Pipeline reads expected column names from config instead of constants. 1-2 day effort |

---

## T10: No Pagination vs Paginated Queries

| | |
|---|---|
| **What we chose** | API returns all records in a single response. Frontend renders them all |
| **What we gained** | Simple implementation, no cursor/offset logic, no infinite scroll |
| **What we lost** | Performance at scale. 10k records in a single JSON response and DOM render will be slow |
| **When it breaks** | Around 2-5k records in the review table. Browser will lag on render, API response will be several MB |
| **Effort to fix** | Low: add DRF's `PageNumberPagination`, update frontend queries to handle paginated responses |
