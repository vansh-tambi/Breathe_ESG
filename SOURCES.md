# Data Sources & References

Last updated: 2026-05-26
Author: engineering (prototype phase)

This document tracks where we got our numbers, what we assumed, and what we made up. Read this before trusting any emission calculation in the prototype.

---

## Emission Factors

### Diesel / Heating Oil
- **Value used:** 2.684 kg CO₂e per liter
- **Source:** Approximate figure from UK DEFRA 2023 conversion factors for liquid fuels (Scope 1, Fuel Oil)
- **Confidence:** Medium. The actual DEFRA value depends on fuel grade (gas oil, burning oil, etc.) and varies between 2.54 and 2.76 kg CO₂e/L. We picked a midpoint.
- **What we didn't do:** Look up the exact DEFRA table row. We should, and the value should be parameterized by fuel type.

### Natural Gas
- **Value used:** 2.021 kg CO₂e per cubic meter
- **Source:** Approximate figure from DEFRA 2023, gross CV natural gas
- **Confidence:** Medium. The real value depends on calorific value (gross vs net) and can range from 1.9 to 2.1. Close enough for prototype calculations.

### Fuel Density (Heating Oil)
- **Value used:** 1 metric ton ≈ 1190 liters
- **Source:** General engineering reference. Diesel/heating oil density is approximately 0.84 kg/L, giving ~1190 L/ton
- **Confidence:** Low-medium. Actual density varies with temperature and fuel composition. Range is roughly 1100-1250 L/ton.

### Flight Travel
- **Value used:** 0.115 kg CO₂e per passenger-kilometer
- **Source:** Loosely based on DEFRA 2023 "Average passenger" for short-haul flights. The actual DEFRA values are:
  - Domestic: ~0.246 kg CO₂e/pkm
  - Short-haul: ~0.151 kg CO₂e/pkm
  - Long-haul: ~0.102 kg CO₂e/pkm
  - We used a rough blended average. This is not rigorous.
- **Confidence:** Low. Without knowing whether a trip is short-haul or long-haul, any single factor is wrong by a factor of 2x. A production system needs to classify by distance or use airport pair lookups.

### Hotel / Ground Transport
- **Value used:** 0.05 kg CO₂e per kilometer
- **Source:** **None. This number is fabricated.**
- **Confidence:** Very low. Hotel emissions are typically calculated per night-stay, not per kilometer. Ground transport factors depend on vehicle type, fuel, and occupancy. We needed a non-zero number so the pipeline doesn't produce all-zero results for these categories. Treat any hotel/ground CO₂e values as placeholder output.

### Electricity (Utility Pipeline)
- **Value used:** Conversion from MWh to kWh (factor of 1000) — no grid emission factor applied in the utility pipeline
- **Source:** Unit conversion only, no emission factor
- **Confidence:** High for the unit conversion, but the pipeline doesn't actually calculate Scope 2 emissions. It normalizes consumption to kWh and stores it. The emission factor step is missing — we'd need grid region-specific emission factors (e.g., eGRID for US, DEFRA for UK, UBA for Germany).

---

## Methodological References

### GHG Protocol
- Corporate Standard (Scope 1 & 2): https://ghgprotocol.org/corporate-standard
- Scope 3 Standard (Category 6 — Business Travel): https://ghgprotocol.org/scope-3-standard
- We claim to follow these categorizations (Scope 1/2/3 classification, activity type mapping). In practice, the prototype implements a simplified version that skips several required disclosures (base year, organizational boundaries, uncertainty assessment).

### DEFRA Conversion Factors
- Published annually by UK Department for Environment, Food & Rural Affairs
- 2023 edition: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023
- We referenced the 2023 factors but did not import the actual spreadsheet. Values were approximated from memory/documentation. A production system should parse the official DEFRA Excel file into an EmissionFactor table.

### SAP Export Format
- The German column headers (Materialbeleg, Buchungsdatum, Werk, Menge, Einheit, Materialtext) are based on a standard SAP MM (Materials Management) transaction export (MIGO/MB51).
- Different SAP configurations may use different column names or include additional fields. Our header validation is strict — any missing expected header rejects the entire file.

### Utility Portal Export Format
- The actual CSV structure (`meter_id`, `billing_period`, `consumption`, `unit`) is based on a simplified format exported by typical electricity utility billing portals.
- The `billing_period` column must hold dates separated by standard delimiters (such as ` - `, ` to `, `-`, or `to`) representing the span of physical consumption. The consumption represents total usage (MWh or kWh) over that specific interval.

### Concur Travel Export
- The assumed CSV structure (Category, Date, Origin, Destination, Distance, Unit) is based on a simplified version of SAP Concur's standard expense export.
- Real Concur exports have 50+ columns. We assume a pre-filtered extract with only the columns we need.

---

## What We're Uncertain About

1. **Whether pro-rata distribution is methodologically acceptable.** GHG Protocol doesn't explicitly prescribe how to allocate multi-period utility bills. Even distribution is common practice but not the only approach. Some frameworks allow first-day-of-period attribution.

2. **Whether storing emission factors as snapshots is sufficient for audit.** Auditors might want to see not just the factor value but the factor source, version, and retrieval date. Our current schema stores the numeric value only.

3. **Whether the flight emission factor approach is GHG Protocol compliant.** Scope 3 Category 6 allows both distance-based and spend-based methods. We use distance-based but with a single blended factor instead of distance-tier-specific factors. This might not pass a third-party verification.

4. **Whether our German decimal parsing handles all edge cases.** German number formatting uses dots for thousands and commas for decimals (e.g., 1.234,56). Our parser handles the common cases but might fail on numbers without thousands separators or with irregular formatting.

5. **Whether UUID primary keys will cause performance issues at scale.** UUIDs are 128 bits and not sequential, which can cause B-tree fragmentation. At prototype volumes this doesn't matter. At millions of rows, we might need to add sequential integer surrogate keys for join performance.

---

## Things We Did Not Research

- Regional grid emission factors for Scope 2 calculations (the utility pipeline doesn't apply them)
- WTT (Well-to-Tank) vs TTW (Tank-to-Wheel) factor separation
- Biogenic vs fossil CO₂ separation in fuel combustion
- Radiative forcing multipliers for aviation emissions
- Market-based vs location-based Scope 2 methodology differences
- Any jurisdiction-specific reporting requirements (EU CSRD, SEC Climate Disclosure, etc.)

These are all things a production system needs to handle. We skipped them because each one is a research and implementation effort of its own.
