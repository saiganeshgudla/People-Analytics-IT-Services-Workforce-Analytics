# ADR-001: PostgreSQL as the Primary Data Warehouse

**Status:** Accepted  
**Date:** 2026-06-24  
**Deciders:** People Analytics Team  

---

## Context

PeopleLens needs a persistent, queryable store for HR data across multiple schemas (raw, staging, marts, analytics). The data is relational (employees, salary, manager hierarchy), requires SCD-2 history for employee records, and must support complex analytical SQL (window functions, CTEs, lateral joins).

## Decision

We use **PostgreSQL 16** as the single data warehouse.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| **SQLite** | No concurrent writes, no schemas, poor window function support |
| **MySQL** | Weaker analytics capabilities, no SCD-2 native support |
| **BigQuery** | Overkill for 10k-employee dataset; billing complexity; local dev friction |
| **DuckDB** | Excellent for local analytics but no persistent server mode for multi-service access |

## Consequences

**Positive:**
- dbt works natively with `dbt-postgres`
- ACID guarantees for data loading
- Schema namespacing (raw / staging / marts / analytics) avoids name collisions
- `generate_series()` and window functions enable complex time-series queries
- Railway offers managed PostgreSQL free tier — no ops burden

**Negative:**
- Requires Docker or Railway for local dev (vs. SQLite zero-setup)
- Mitigation: `database.py` falls back to SQLite automatically if PG unavailable
