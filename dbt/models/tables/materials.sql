select m.id
     , empty_str2null(m.doc -> 'properties' ->> 'cclom:title')                                title
     , empty_jsonb_array2null(m.doc -> 'properties' -> 'cclom:general_description')           description
     , empty_jsonb_array2null(m.doc -> 'properties' -> 'cclom:general_keyword')               keywords
     , empty_jsonb_array2null(m.doc -> 'properties' -> 'ccm:taxonid')                         taxon_id
     , empty_jsonb_array2null(m.doc -> 'properties' -> 'ccm:educationalcontext')              edu_context
     , empty_jsonb_array2null(m.doc -> 'properties' -> 'ccm:commonlicense_key')               license
     , empty_str2null(m.doc -> 'properties' ->> 'ccm:objecttype')                             object_type
     , empty_str2null(m.doc -> 'properties' ->> 'ccm:containsAdvertisement')                  ads_qualifier
     , empty_jsonb_array2null(m.doc -> 'properties' -> 'ccm:oeh_lrt_aggregated') learning_resource_type
     , empty_jsonb_array2null(m.doc -> 'properties' -> 'ccm:educationalintendedenduserrole')  intended_enduser_role
     , empty_str2null(m.doc -> 'properties' ->> 'ccm:wwwurl')                                 url
     , empty_str2null(m.doc -> 'properties' ->> 'ccm:replicationsource')                      replication_source
     , empty_str2null(m.doc -> 'properties' ->> 'ccm:replicationsourceid')                    replication_source_id
     , to_timestamp((m.doc -> 'properties' ->> 'cm:created')::bigint / 1000)                  created
     , to_timestamp((m.doc -> 'properties' ->> 'cm:modified')::bigint / 1000)                 modified
     , m.doc
from {{ source('elastic_wlo', 'materials') }} m
