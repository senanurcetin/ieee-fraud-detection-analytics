select
    *,
    case
        when transaction_amount < 25 then '01. <$25'
        when transaction_amount < 50 then '02. $25-49'
        when transaction_amount < 100 then '03. $50-99'
        when transaction_amount < 250 then '04. $100-249'
        when transaction_amount < 500 then '05. $250-499'
        else '06. $500+'
    end as amount_band,
    coalesce(product_cd, 'Unknown') as product_cd_clean,
    coalesce(card4, 'Unknown') as card_network,
    coalesce(card6, 'Unknown') as card_type,
    coalesce(device_type, 'Unknown') as device_type_clean,
    case
        when lower(coalesce(p_emaildomain, '')) in ('gmail.com', 'yahoo.com', 'hotmail.com', 'anonymous.com', 'aol.com', 'comcast.net') then lower(p_emaildomain)
        when p_emaildomain is null then 'Unknown'
        else 'Other'
    end as purchaser_email_group,
    case
        when transaction_week <= 4 then 'Early'
        when transaction_week <= 8 then 'Middle'
        else 'Late'
    end as time_window
from {{ ref('int_fraud_joined') }}
