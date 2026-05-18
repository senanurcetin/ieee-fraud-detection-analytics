{% test accepted_range(model, column_name, min_value=None, max_value=None, inclusive=True) %}
select *
from {{ model }}
where {{ column_name }} is not null
  and (
    1 = 0
    {% if min_value is not none %}
      or {{ column_name }} {% if inclusive %}<{% else %}<={% endif %} {{ min_value }}
    {% endif %}
    {% if max_value is not none %}
      or {{ column_name }} {% if inclusive %}>{% else %}>={% endif %} {{ max_value }}
    {% endif %}
  )
{% endtest %}

{% test not_negative(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} < 0
{% endtest %}

{% test row_count_equals(model, expected_count) %}
select count(*) as actual_count
from {{ model }}
having count(*) != {{ expected_count }}
{% endtest %}

{% test row_count_between(model, min_count, max_count) %}
select count(*) as actual_count
from {{ model }}
having count(*) < {{ min_count }} or count(*) > {{ max_count }}
{% endtest %}

{% test fraud_rate_between(model, column_name, min_value=0, max_value=1) %}
select *
from {{ model }}
where {{ column_name }} is not null
  and ({{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }})
{% endtest %}
