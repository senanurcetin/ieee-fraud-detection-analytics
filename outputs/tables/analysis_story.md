# Analysis Story

## Central Question

Where does fraud concentrate, and how should a BI team monitor it?

## Key Findings

1. Fraud is rare but concentrated: baseline fraud rate is 3.50%.
2. Product risk is uneven: Product C fraud rate is 11.69% versus Product W at 2.04%.
3. Identity presence is a risk signal: identity-present transactions show 7.85% fraud versus 2.09% without identity records.
4. Amount risk is non-linear: <$25 and $250+ bands show higher fraud rates than mid-size purchases.
5. Payment attributes matter: credit card combinations over-index versus debit card combinations.
6. The model should be used as a monitoring/ranking layer: Critical risk band captures very high fraud-rate lift versus baseline.

## Recommended Narrative

Start with class imbalance, then prove that fraud is not random. Move through product, identity, amount, payment, email, and time patterns. End with model risk bands as an operational monitoring layer, not as a black-box final decision engine.
