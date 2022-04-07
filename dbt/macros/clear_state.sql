{% macro clear_state() %}

{% set sql %}
truncate {{ source('elastic_wlo', 'collections') }};
truncate {{ source('elastic_wlo', 'materials') }};
truncate {{ source('elastic_wlo', 'collections_previous_run') }};
truncate {{ source('elastic_wlo', 'materials_previous_run') }};
{% endset %}

{% do run_query(sql) %}
{% do log("State cleared by truncating tables", info=True) %}

{% endmacro %}
