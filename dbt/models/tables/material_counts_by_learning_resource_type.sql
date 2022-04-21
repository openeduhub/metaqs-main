with stacked as (

    select m.id
         , cm.collection_id
         , jsonb_array_elements_text(m.learning_resource_type) learning_resource_type
    from {{ ref('materials') }} m
             join {{ ref('collection_material_ext') }} cm on cm.material_id = m.id

), counts as (

    select st.collection_id
         , st.learning_resource_type
         , count(*) count
    from stacked st
    group by st.collection_id, st.learning_resource_type

), final as (

    select counts.*
         , shorten_vocab(learning_resource_type, 'oeh_lrt_aggregated') short_learning_resource_type
    from counts

)

select *
from final
