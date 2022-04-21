select c.id                      resource_id
     , 'COLLECTION'::resource_type resource_type
     , unnest(
        string_to_array(
                concat_ws(
                        ','
                    , case when c.title isnull then 'TITLE' end
                    , case when c.description isnull then 'DESCRIPTION' end
                    , case when c.keywords isnull then 'KEYWORDS' end
                    , case when c.edu_context isnull then 'EDU_CONTEXT' end
                    )
            , ','
            )
    )::resource_field            missing_field
from {{ ref('collections') }} c

union all
select m.id                      resource_id
     , 'MATERIAL'::resource_type resource_type
     , unnest(
        string_to_array(
                concat_ws(
                        ','
                    , case when m.title isnull then 'TITLE' end
                    , case when m.description isnull then 'DESCRIPTION' end
                    , case when m.license isnull then 'LICENSE' end
                    , case when m.taxon_id isnull then 'TAXON_ID' end
                    , case when m.edu_context isnull then 'EDU_CONTEXT' end
                    , case when m.learning_resource_type isnull then 'LEARNING_RESOURCE_TYPE' end
                    , case when m.keywords isnull then 'KEYWORDS' end
                    , case when m.ads_qualifier isnull then 'ADS_QUALIFIER' end
                    , case when m.object_type isnull then 'OBJECT_TYPE' end
                    )
            , ','
            )
    )::resource_field            missing_field
from {{ ref('materials') }} m
