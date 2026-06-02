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
    case when f.addr1 is not null or f.addr2 is not null then 1 else 0 end as has_address_proxy,
    case when f.dist1 is not null or f.dist2 is not null then 1 else 0 end as has_distance_proxy,
    case
        when f.addr1 is null and f.addr2 is null then 'Address missing'
        when f.addr1 is not null and f.addr2 is not null then 'Address both present'
        else 'Address partial'
    end as address_proxy_status,
    case
        when f.dist1 is null and f.dist2 is null then 'Distance missing'
        when coalesce(abs(f.dist1), abs(f.dist2), 0) < 10 then 'Distance low'
        when coalesce(abs(f.dist1), abs(f.dist2), 0) < 100 then 'Distance medium'
        else 'Distance high'
    end as distance_proxy_band,
    f.is_fraud,
    p.predicted_fraud_probability,
    p.risk_band,
    case when p.risk_band = 'Critical' then 1 else 0 end as is_critical_risk,
    case when p.risk_band in ('High', 'Critical') then 1 else 0 end as is_high_or_critical_risk
from {{ ref('int_features') }} as f
left join {{ ref('mart_model_predictions') }} as p
    on f.transaction_id = p.transaction_id
    and p.split = 'train'
