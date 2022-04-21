{% set resource_is_modified %}
    ((fresh.doc -> 'properties' ->> 'cm:modified')::bigint
        > (previous.doc -> 'properties' ->> 'cm:modified')::bigint)
{% endset %}

{% set select_collections %}
    select fresh.id                    resource_id
         , 'COLLECTION'::resource_type resource_type
         , unnest(array [
            'TITLE',
            'DESCRIPTION'
        ])::resource_field             resource_field
         , unnest(array [
            empty_str2null(fresh.doc -> 'properties' ->> 'cm:title')
          , empty_str2null(fresh.doc -> 'properties' ->> 'cm:description')
        ])                             text_content
         , fresh.derived_at
{% endset %}

{% set select_materials %}
    select fresh.id                    resource_id
         , 'MATERIAL'::resource_type   resource_type
         , unnest(array [
            'TITLE'
        ])::resource_field             resource_field
         , unnest(array [
            empty_str2null(fresh.doc -> 'properties' ->> 'cclom:title')
        ])                             text_content
         , fresh.derived_at
{% endset %}


with cte as (

    -- fresh collections
    {{ select_collections }}
    from {{ source('elastic_wlo', 'collections') }} fresh
    where fresh.id not in (
        select id
        from {{ source('elastic_wlo', 'collections_previous_run') }}
    )

    union
    -- updated collections
    {{ select_collections }}
    from {{ source('elastic_wlo', 'collections') }} fresh
             join {{ source('elastic_wlo', 'collections_previous_run') }} previous using (id)
    where {{ resource_is_modified }}


    union
    -- fresh materials
    {{ select_materials }}
    from {{ source('elastic_wlo', 'materials') }} fresh
    where fresh.id not in (
        select id
        from {{ source('elastic_wlo', 'materials_previous_run') }}
    )

    union
    -- updated materials
    {{ select_materials }}
    from {{ source('elastic_wlo', 'materials') }} fresh
             join {{ source('elastic_wlo', 'materials_previous_run') }} previous using (id)
    where {{ resource_is_modified }}
)

select distinct *
from cte
where text_content is not null
order by resource_id, resource_field
