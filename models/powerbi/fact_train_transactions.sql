select
    f.transaction_id,
    f.transaction_day,
    f.transaction_week,
    f.time_window,
    f.transaction_hour,
    f.relative_day_of_week,
    f.transaction_amount,
    f.transaction_amount_cents,
    f.is_round_amount,
    f.amount_band,
    f.product_cd_clean as product_cd,
    f.card_network,
    f.card_type,
    f.device_type_clean as device_type,
    f.purchaser_email_group,
    f.purchaser_email_risk_group,
    f.has_identity,
    f.synthetic_uid_card_addr,
    f.is_fraud,
    p.predicted_fraud_probability,
    p.risk_band,
    case when p.risk_band = 'Critical' then 1 else 0 end as is_critical_risk,
    case when p.risk_band in ('High', 'Critical') then 1 else 0 end as is_high_or_critical_risk
from {{ ref('int_features') }} as f
left join {{ ref('mart_model_predictions') }} as p
    on f.transaction_id = p.transaction_id
    and p.split = 'train'
