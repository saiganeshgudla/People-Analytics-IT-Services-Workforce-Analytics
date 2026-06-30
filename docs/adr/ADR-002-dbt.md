# ADR-002: dbt for Analytics Engineering

**Status:** Accepted  
**Date:** 2026-06-24  
**Deciders:** People Analytics Team  

---

## Context

HR data arrives in raw form (messy CSVs with nulls, duplicates, inconsistent formats). We need a transformation layer to clean, model, and document the data before it reaches the analytics engine. The transformation logic needs to be version-controlled, testable, and reproducible.

## Decision

We use **dbt (data build tool)** for all SQL-based transformations.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| **Raw SQL scripts** | No dependency graph, no tests, no documentation, no lineage |
| **Pandas pipelines** | Harder to debug in SQL, no column-level lineage, not declarative |
| **SQLMesh** | Less mature, smaller community, steeper learning curve |
| **Apache Spark** | Massively overengineered for 10k employees |

## Consequences

**Positive:**
- Every model is a `.sql` file — version-controlled and reviewable
- `dbt test` catches data quality issues automatically (null checks, uniqueness, accepted values)
- `dbt docs generate` creates a browsable data catalog
- SCD-2 snapshots for `dim_employee` are built-in via `dbt snapshot`
- Industry standard: used at Airbnb, Spotify, GitHub

**Negative:**
- Requires `dbt-postgres` installed alongside the main app
- Local execution requires PostgreSQL (mitigated by docker-compose setup)
- Learning curve for team members unfamiliar with Jinja + SQL combination
