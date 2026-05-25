with train_days as (
    select count(distinct transaction_day) as observed_days
    from {{ ref('fact_train_transactions') }}
),

bands as (
    select *
    from {{ ref('rpt_model_risk_bands') }}
    where split = 'train'
)

select
    b.risk_band,
    b.band_rank,
    b.review_priority,
    b.transaction_count,
    b.avg_predicted_probability,
    b.observed_fraud_count,
    b.observed_fraud_rate,
    b.baseline_observed_fraud_rate,
    b.lift,
    b.transaction_share,
    b.expected_fraud_capture,
    {{ fp_float('b.transaction_count') }} / nullif({{ fp_float('d.observed_days') }}, 0) as estimated_daily_review_volume,
    case
        when b.risk_band = 'Critical' then 'AnlÄ±k inceleme kuyruÄŸu'
        when b.risk_band = 'High' then 'AynÄ± gÃ¼n Ã¶ncelikli inceleme'
        when b.risk_band = 'Elevated' then 'Ã–rneklem bazlÄ± manuel kontrol'
        else 'Otomatik izleme'
    end as queue_policy,
    case
        when b.risk_band in ('Critical', 'High') then 'Operasyon kapasitesi ayrÄ±lmalÄ±'
        when b.risk_band = 'Elevated' then 'Kural performansÄ± haftalÄ±k izlenmeli'
        else 'Ek aksiyon gerektirmez'
    end as management_note
from bands as b
cross join train_days as d
order by b.band_rank
