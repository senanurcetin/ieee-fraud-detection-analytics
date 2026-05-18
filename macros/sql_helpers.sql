{% macro fp_quote(identifier) -%}
    {{ adapter.quote(identifier) }}
{%- endmacro %}

{% macro fp_int(expr) -%}
    cast({{ expr }} as {{ 'int64' if target.type == 'bigquery' else 'bigint' }})
{%- endmacro %}

{% macro fp_smallint(expr) -%}
    cast({{ expr }} as {{ 'int64' if target.type == 'bigquery' else 'integer' }})
{%- endmacro %}

{% macro fp_float(expr) -%}
    cast({{ expr }} as {{ 'float64' if target.type == 'bigquery' else 'double' }})
{%- endmacro %}

{% macro fp_string(expr) -%}
    cast({{ expr }} as {{ 'string' if target.type == 'bigquery' else 'varchar' }})
{%- endmacro %}

{% macro fp_avg_rate(expr) -%}
    avg({{ fp_float(expr) }})
{%- endmacro %}

{% macro fp_percentile(expr, percentile) -%}
    {%- if target.type == 'bigquery' -%}
        approx_quantiles({{ expr }}, 100)[offset({{ (percentile * 100) | int }})]
    {%- else -%}
        quantile_cont({{ expr }}, {{ percentile }})
    {%- endif -%}
{%- endmacro %}
