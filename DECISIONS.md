# Architecture & Design Decisions

Last updated: 2026-05-26
Author: engineering (prototype phase)

---

## D1: Monolith over Microservices

**Decision:** Single Django project, single PostgreSQL database, single repository.

**Why:** Four-day prototype. Microservices introduce deployment orchestration, service discovery, network serialization overhead, and distributed transaction problems. None of which we need. The ingestion → normalization → review pipeline is a synchronous linear flow that fits naturally in a single process.

**Alternative rejected:** Separate ingestion service + normalization worker + review API. Would require message queuing (RabbitMQ/Kafka), separate deployments, and at least two databases. The operational overhead is unjustifiable for a prototype that handles maybe 10k rows per upload.

**When to revisit:** If ingestion volumes exceed what a single Django worker can handle synchronously (probably around 500k rows per upload), or if the team grows beyond 4 engineers and needs independent deploy cycles.

---

## D2: Synchronous CSV Processing

**Decision:** CSV files are parsed and normalized inside the HTTP request cycle, wrapped in a single database transaction.

**Why:** Simplicity. The upload → parse → normalize → respond flow completes in under a second for typical file sizes (< 5000 rows). Adding Celery or background workers doubles the infrastructure complexity and introduces polling/webhook patterns on the frontend.

**Alternative rejected:** Celery + Redis background task queue. Would allow the upload endpoint to return 202 Accepted immediately and process asynchronously. Better for large files but requires Redis, Celery worker process, task status polling endpoint, and failure retry logic. That's 2+ days of work for a problem we don't actually have yet.

**Tradeoff accepted:** Large files (50k+ rows) will cause HTTP timeout. We're accepting this limit for the prototype.

---

## D3: Raw + Normalized Two-Table Pattern

**Decision:** Store every CSV row twice — once as raw JSON (RawRecord), once as structured normalized data (NormalizedRecord).

**Why:** Compliance requirement. ESG auditors need to see exactly what the source system produced, not just our interpretation of it. If our normalization logic has a bug (and it probably does — see the hardcoded emission factors), we can re-process from raw data without re-uploading.

**Alternative rejected:** Single table with both raw and normalized columns. Simpler schema but violates the principle that raw data should be immutable. If normalization columns live on the same row, there's nothing preventing accidental overwrites of the original values.

**Alternative rejected:** Store original CSV files as blobs. Preserves the original but makes per-row error reporting require re-parsing the file every time. Row-level JSON storage trades disk space for operational convenience.

---

## D4: Hardcoded Emission Factors

**Decision:** Emission factors (kg CO₂e per unit) are hardcoded as Python constants in the pipeline modules.

**Why:** Building a proper emission factor database (with source tracking, version history, effective date ranges, regional variants) is easily a week of dedicated work. For a 4-day prototype, hardcoded values demonstrate the calculation flow without the infrastructure.

**What we hardcoded:**
- Diesel/Heating Oil: 2.684 kg CO₂e per liter (DEFRA 2023 approximate)
- Natural Gas: 2.021 kg CO₂e per cubic meter
- Flights: 0.115 kg CO₂e per passenger-km (short-haul average)
- Hotel/Ground: 0.05 kg CO₂e per km (placeholder — this number is made up)
- Electricity: depends on grid region but currently uses a flat conversion

**Honest assessment:** The hotel/ground travel factor is not based on any published methodology. It exists so the pipeline doesn't crash on non-flight travel rows. In production, this needs a proper factor registry keyed on (category, region, year).

---

## D5: Company FK Denormalization

**Decision:** Both RawRecord and NormalizedRecord carry a direct FK to Company, even though the company is derivable through DataSource.

**Why:** Every single API query is tenant-scoped. The alternative is `NormalizedRecord.objects.filter(raw_record__data_source__company=company)`, which is a three-table JOIN on what might become the highest-volume table. The denormalized FK gives us `NormalizedRecord.objects.filter(company=company)` — one indexed scan.

**Tradeoff:** If a DataSource is somehow moved between companies (which shouldn't happen but never say never), the denormalized company FK on child records would be stale. We accepted this because tenant migration is an admin-level operation that would require a data migration script anyway.

---

## D6: No Authentication in Prototype

**Decision:** All endpoints use `AllowAny` permission. No login, no tokens, no session management.

**Why:** The prototype is for demonstrating the data pipeline, not the auth flow. Adding JWT/session auth is a well-understood problem that can be bolted on in a day. Spending prototype time on it would displace actual domain logic.

**How we handle multi-tenancy without auth:** The frontend passes `company_id` as a query parameter. This is obviously insecure — any client can query any tenant's data. Acceptable for prototype, completely unacceptable for production.

**What production needs:** Django REST Framework's `TokenAuthentication` or `SimpleJWT`, a middleware that extracts tenant from the token, and removal of the `company_id` query param pattern.

---

## D7: Review Workflow as Separate Endpoints

**Decision:** Five separate endpoints (GET records, GET suspicious, POST approve, POST reject, POST lock) rather than a single PATCH endpoint with an action parameter.

**Why:** Each action has different validation rules and side effects. Approve sets `is_locked=True`. Reject does not. Lock is idempotent on already-locked rows. Cramming this into one endpoint with `action=approve|reject|lock` in the body means a switch statement that grows with every new action type. Separate endpoints are easier to document, test, and extend.

**Alternative rejected:** Single `PATCH /review/records/{id}/` with body `{"action": "approve", "notes": "..."}`. Technically RESTful but conflates different operations under one URL. Also makes API logging less useful — you can't tell from the URL alone what happened.

---

## D8: Frontend with React Query (No Redux/Context)

**Decision:** All server state lives in React Query's cache. No global state management library.

**Why:** Every piece of state in this app is server-derived. There's no client-only state complex enough to justify Redux. React Query handles caching, refetching, loading/error states, and cache invalidation after mutations. Adding Redux on top would mean duplicating server state into a store and manually keeping it in sync.

**Alternative rejected:** Redux Toolkit + RTK Query. More boilerplate, same result. RTK Query is essentially React Query with Redux bindings we don't need.

**Alternative rejected:** React Context for "current company" state. Considered it but decided a hardcoded default company ID is more honest for a prototype. Context would add an abstraction layer pretending we have a proper tenant selection flow, which we don't.

---

## D9: Tailwind CSS v4 (via Vite Plugin)

**Decision:** Tailwind v4 with `@tailwindcss/vite` plugin. No `tailwind.config.js` — Tailwind v4 uses CSS-first configuration.

**Why:** Tailwind v4's Vite plugin is zero-config. No PostCSS setup, no config file, just `@import "tailwindcss"` in CSS and the plugin in `vite.config.js`. Faster build times than v3.

**What's different from v3:** No `tailwind.config.js` or `postcss.config.js` needed. Content detection is automatic. Theme customization happens in CSS with `@theme` blocks rather than JavaScript config. We use CSS custom properties (`:root` variables) for our color tokens instead of extending the Tailwind theme, which keeps things simple.

---

## D10: Pro-Rata Date Splitting (Utility Pipeline)

**Decision:** Utility billing periods that span multiple months are split into daily pro-rata allocations.

**Why:** ESG reporting is monthly or quarterly. A billing period of "Jan 15 – Mar 15" can't be assigned to a single month without distorting the numbers. Pro-rata splitting distributes consumption evenly across the period.

**Simplification admitted:** Even distribution is naive. Real electricity consumption is not uniform — it varies by season, weekday/weekend, operational schedule. Proper allocation would use degree-day models or load curves. We use even distribution because we don't have the data to do better.

---

## D11: Travel Distance as Primary Metric

**Decision:** Travel emissions are calculated from distance (km), not from fare amount or fuel burned.

**Why:** Distance-based emission factors are the standard methodology in GHG Protocol Scope 3 Category 6 (Business Travel). Fare-based methods exist but require spend-to-emission conversion tables that vary by airline, class, and route.

**Problem:** Concur exports often don't include distance. The pipeline stores `distance_km = None` for rows with missing distance data, and sets CO₂e to zero. This means missing-distance rows are effectively ignored in emissions totals. In production, we'd need a distance estimation service (e.g., IATA airport-pair distance database) as a fallback.
