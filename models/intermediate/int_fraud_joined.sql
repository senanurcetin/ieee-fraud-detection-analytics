select
    t.*,
    i.id_01,
    i.id_02,
    i.id_05,
    i.id_06,
    i.id_11,
    i.id_13,
    i.id_17,
    i.id_19,
    i.id_20,
    i.id_12,
    i.id_15,
    i.id_16,
    i.id_28,
    i.id_29,
    i.id_31,
    i.id_35,
    i.id_36,
    i.id_37,
    i.id_38,
    i.device_type,
    i.device_info,
    case when i.transaction_id is null then 0 else 1 end as has_identity
from {{ ref('stg_transactions') }} as t
left join {{ ref('stg_identity') }} as i
    on t.transaction_id = i.transaction_id
