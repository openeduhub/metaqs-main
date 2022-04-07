-- removed collections
select c_pr.id
from {{ source('elastic_wlo', 'collections_previous_run') }} c_pr
where c_pr.id not in (
    select id from {{ source('elastic_wlo', 'collections') }}
)

union
-- removed materials
select m_pr.id
from {{ source('elastic_wlo', 'materials_previous_run') }} m_pr
where m_pr.id not in (
    select id from {{ source('elastic_wlo', 'materials') }}
)
