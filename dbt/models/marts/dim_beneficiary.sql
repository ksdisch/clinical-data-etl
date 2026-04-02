select
    bene_id,
    date_of_birth,
    date_of_death,
    gender,
    race,
    renal_disease_indicator,
    state_code,
    county_code,
    months_part_a_coverage,
    months_part_b_coverage,

    -- Chronic conditions
    has_alzheimers,
    has_heart_failure,
    has_kidney_disease,
    has_cancer,
    has_obstr_pulmonary,
    has_depression,
    has_diabetes,
    has_ischemic_heart,
    has_osteoporosis,
    has_rheumatoid_arthritis,
    has_stroke,

    -- Aggregates
    ip_annual_reimbursement  as total_ip_reimbursement,
    op_annual_reimbursement  as total_op_reimbursement,

    -- Chronic condition count
    (
        has_alzheimers::int
        + has_heart_failure::int
        + has_kidney_disease::int
        + has_cancer::int
        + has_obstr_pulmonary::int
        + has_depression::int
        + has_diabetes::int
        + has_ischemic_heart::int
        + has_osteoporosis::int
        + has_rheumatoid_arthritis::int
        + has_stroke::int
    ) as chronic_condition_count

from {{ ref('stg_beneficiary') }}
