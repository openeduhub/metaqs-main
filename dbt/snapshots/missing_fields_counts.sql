{% snapshot missing_fields_counts %}

    {{
        config(
          strategy='check',
          unique_key='collection_id',
          check_cols=[
              'total',
              'title',
              'description',
              'keywords',
              'license',
              'taxon_id',
              'learning_resource_type',
              'ads_qualifier',
              'object_type',
          ],
        )
    }}

    select fresh.*
    from {{ ref('material_counts_by_missing_field') }} fresh

{% endsnapshot %}
