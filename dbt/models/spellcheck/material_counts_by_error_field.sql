with s1 as (

    select distinct sp.resource_id
                  , sp.resource_field
    from {{ ref('spellcheck') }} sp
    where sp.resource_type = 'MATERIAL'

), agg as (

    select cm.collection_id
         , count(s1.resource_field) filter ( where s1.resource_field = 'TITLE' ) title
         , count(s1.resource_field) filter ( where s1.resource_field = 'DESCRIPTION' ) description
    from s1
            left join {{ ref('collection_material_ext') }} cm on cm.material_id = s1.resource_id
    group by cm.collection_id, s1.resource_field

)

select c.id                         collection_id
     , c.portal_title
     , coalesce(agg.title, 0)       title
     , coalesce(agg.description, 0) description
from {{ ref('collections') }} c
        left join agg on agg.collection_id = c.id
