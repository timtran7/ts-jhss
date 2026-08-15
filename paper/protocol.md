# Sprint 1 protocol — DCSAA boys Kenilworth era

## Question
Does last year’s pack (5th runner) tell you more about this year’s DCSAA boys team place than last year’s star (1st runner), after sector and enrollment?

## Unit
Team-season. Scoring teams only in the primary OLS (five finishers).

## Outcome
`state_place` (and `state_score` as sensitivity) at the DCSAA varsity boys 5k, Kenilworth Park.

## Predictors (no leakage)
Computed from the **previous Kenilworth championship** (or previous available season; 2021 lags to 2019):
- `lag_star_z`: within-meet z of the team’s #1 time
- `lag_depth_z`: within-meet z of the team’s #5 time
- `lag_pack_gap`: lag_depth_z − lag_star_z
- Controls: `log_enrollment`, sector dummies (private as reference vs public/charter)
- H2: `wcac` (Gonzaga, St. John’s, Archbishop Carroll)

## Split
Fit 2017–2024 (rows with non-missing lags). Freeze. Evaluate 2025.

## Estimators
OLS with school-clustered standard errors. Nested models: controls → +star → +depth → +both → +wcac. Compare AIC on the fit set; holdout RMSE/Spearman from the AIC-best depth model. Team score is a sensitivity outcome.

## Secondary
If invitational files exist: team–meet panel with cluster-robust SEs. Not the headline table.

## Exclusion
2020. Non-5k. JV / Varsity B / MS. Same-year championship times as features.
