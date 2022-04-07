{% macro proportion(count, total) %}
round({{ count }}::numeric / {{ total }}::numeric, 3) * 100
{% endmacro %}
