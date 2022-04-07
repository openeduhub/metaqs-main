select cm.collection_id
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'TITLE' )                 title
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'DESCRIPTION' )           description
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'KEYWORDS' )              keywords
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'LICENSE' )               license
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'TAXON_ID' )              taxon_id
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'EDU_CONTEXT' )           edu_context
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'LEARNING_RESOURCE_TYPE' ) learning_resource_type
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'ADS_QUALIFIER' )         ads_qualifier
     , count(distinct cm.material_id)
       filter ( where f.missing_field = 'OBJECT_TYPE' )           object_type
from {{ ref('missing_fields') }} f
         join {{ ref('collection_material_ext') }} cm on cm.material_id = f.resource_id
where f.resource_type = 'MATERIAL'
group by cm.collection_id