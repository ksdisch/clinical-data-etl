-- Conformed lookup dimension for the diabetes star, built from the
-- admission_type_mapping seed. Turns the opaque admission_type_id integer on
-- fct_encounters into a labelled category (Emergency, Urgent, Elective, …).

select
    admission_type_id,
    admission_type_label
from {{ ref('admission_type_mapping') }}
