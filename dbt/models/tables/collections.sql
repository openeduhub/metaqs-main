{% set portal_root_id_segment = var('portal_root_id').replace('-', '_') %}

with processed_paths as (

    select c.id
         , (select text2ltree(
                           txt2ltxt(
                                   string_agg(
                                           path_segments,
                                           '.'
                                       )
                               )
                       ) || uuid2ltree(c.id)
            from jsonb_array_elements_text(c.doc -> 'path') path_segments)           path
         , empty_str2null(c.doc -> 'properties' ->> 'cm:title')                      title
         , empty_str2null(c.doc -> 'properties' ->> 'cm:description')                description
         , empty_jsonb_array2null(c.doc -> 'properties' -> 'cclom:general_keyword')  keywords
         , empty_jsonb_array2null(c.doc -> 'properties' -> 'ccm:taxonid')            taxon_id
         , empty_jsonb_array2null(c.doc -> 'properties' -> 'ccm:educationalcontext') edu_context
         , c.doc
    from {{ source('elastic_wlo', 'collections') }} c

), processed_collections as (

    select c.*
         , ltree2uuid(subpath(subpath(c.path, index(c.path, '{{ portal_root_id_segment }}') + 1), 0, 1)) portal_id
         , nlevel(subpath(c.path, index(c.path, '{{ portal_root_id_segment }}') + 1)) - 1                portal_depth
         , subpath(c.path, index(c.path, '{{ portal_root_id_segment }}') + 1)                            portal_path
     from processed_paths c

), final as (

    select c.*
         , coalesce(c2.title, c2.id::text) portal_title
    from processed_collections c
        join processed_collections c2 on c2.id = c.portal_id

)

select *
from final
order by portal_depth, id
