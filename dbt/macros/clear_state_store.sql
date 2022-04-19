{% macro clear_state_store() %}

{% set sql %}
truncate {{ source('languagetool', 'spellcheck') }};
truncate {{ source('elastic_wlo', 'search_stats') }};
{% endset %}

{% do run_query(sql) %}
{% do log("Store state cleared by truncating tables", info=True) %}

{% endmacro %}
