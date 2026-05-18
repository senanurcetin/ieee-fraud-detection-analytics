select
    f.transaction_id,
    f.transaction_day,
    f.transaction_week,
    f.time_window,
    {{ fp_smallint("floor(mod(f.transaction_dt, 86400) / 3600)") }} as transaction_hour,
    f.transaction_amount,
    f.amount_band,
    f.product_cd_clean as product_cd,
    f.card_network,
    f.card_type,
    f.device_type_clean as device_type,
    f.purchaser_email_group,
    f.has_identity,
    f.is_fraud,
    p.predicted_fraud_probability,
    p.risk_band,
    case when p.risk_band = 'Critical' then 1 else 0 end as is_critical_risk,
    case when p.risk_band in ('High', 'Critical') then 1 else 0 end as is_high_or_critical_risk
from {{ ref('int_features') }} as f
left join {{ ref('mart_model_predictions') }} as p
    on f.transaction_id = p.transaction_id
    and p.split = 'train'
