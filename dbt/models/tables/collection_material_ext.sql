with stacked as (

    select cm.material_id
         , unnest(ltree2uuids(c.portal_path)) collection_id
    from {{ ref('collection_material') }} cm
        join {{ ref('collections') }} c on c.id = cm.collection_id

)

select distinct *
from stacked
where collection_id != '{{ var("portal_root_id") }}'::uuid
