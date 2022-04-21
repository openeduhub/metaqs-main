select cm.collection_id
     , f.missing_field
     , count(distinct cm.material_id)     count
     , jsonb_agg(distinct cm.material_id) material_ids
from {{ ref('missing_fields') }} f
         join {{ ref('collection_material_ext') }} cm on cm.material_id = f.resource_id
where f.resource_type = 'MATERIAL'
group by cm.collection_id, f.missing_field
order by collection_id, missing_field
