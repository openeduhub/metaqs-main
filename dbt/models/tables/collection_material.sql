with stacked as (

    select m.id                                                                       material_id
         , (jsonb_array_elements(m.doc -> 'collections') -> 'nodeRef' ->> 'id')::uuid collection_id
    from {{ ref('materials') }} m
)

select stacked.*
from stacked
        join {{ ref('collections') }} c on c.id = stacked.collection_id
