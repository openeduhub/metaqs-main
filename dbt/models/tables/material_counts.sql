select c.id                                        collection_id
     , coalesce(count(distinct cm.material_id), 0) total
from {{ ref('collections') }} c
         left join {{ ref('collection_material_ext') }} cm
on cm.collection_id = c.id
group by c.id
