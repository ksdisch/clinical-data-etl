# ADR-002: Keep the fraud label in `dim_provider`, not on `fct_claims`

**Status:** Accepted

## Context

`PotentialFraud` is a property of a **provider**, not of an individual claim — the source labels
whole providers as potentially fraudulent, and every claim under a flagged provider inherits that
context only transitively. It is tempting to denormalise the flag onto `fct_claims` so that
"fraudulent claims" can be filtered without a join. Doing so would corrupt the fact grain: a claim
does not *have* a fraud status, so a `is_potential_fraud` column on `fct_claims` would assert a fact
about claims that the data does not support, and would silently double-count fraud prevalence when
aggregated at the claim level instead of the provider level.

## Decision

The fraud label lives only on `dim_provider` (`dbt/models/marts/dim_provider.sql`). `fct_claims`
carries `provider_id` as a foreign key; any fraud analysis joins `fct_claims` → `dim_provider` on
`provider_id`. The SCD2 history of the label is a separate dimension (`dim_provider_history`,
see ADR-007), again keyed on the provider, never the claim.

## Consequences

- **Easier:** the star stays honest — each fact and dimension asserts only facts at its own grain;
  fraud prevalence is computed at the provider grain where it is meaningful.
- **Harder / accepted:** "show me fraudulent claims" requires a join rather than a single-table scan.
  This is the correct cost of a correct grain, and it is the standard dimensional-modelling pattern a
  reviewer expects to see.
