# ADR-003: Reject-and-continue validation; orphan claims as a warn

**Status:** Accepted

## Context

pandera validates every table at ingestion. Some real source rows fail — most notably ~30 beneficiary
rows that violate the `BeneficiarySchema` constraints. Two questions follow: (1) what happens to a bad
row, and (2) what happens to otherwise-valid claims that reference a rejected beneficiary (orphans).
A strict fail-fast pipeline would abort the whole run on the first bad row; a silent-drop pipeline
would lose data with no audit trail. The 30 rejected beneficiaries leave ~88 claims in `fct_claims`
whose `bene_id` has no match in `dim_beneficiary`.

## Decision

**Reject-and-continue.** Rows that fail pandera are written to `data/rejected/` (e.g.
`beneficiary_rejected.csv`) and the valid remainder continues through the pipeline — so a bad row is
auditable, not fatal and not invisible.

For the resulting orphan claims, the `relationships` test on `fct_claims.bene_id → dim_beneficiary`
is set to **`severity: warn`** (`dbt/models/marts/schema.yml`), not `error`. The provider relationship
stays a hard `error`. This makes the orphan situation visible on every `dbt test` run without failing
CI over a known, quantified, intentional data-quality artifact.

## Consequences

- **Easier:** the pipeline is resilient to dirty source data and keeps a quarantine trail; CI stays
  green while still surfacing the orphan count.
- **Harder / accepted:** analysts must know that `fct_claims` can contain a small number of claims with
  no beneficiary dimension row. This is documented here, in the schema test comment, and in the data
  dictionary. A production system would additionally alert on reject *volume* (a spike means an upstream
  schema change), which is noted as future work rather than built.
