# Analysis rules

Among schools with an eligible prior championship, prior fifth-runner relative time (within-meet z; higher = slower) should predict next championship team place more accurately than prior first-runner relative time, after log enrollment and sector.

More accurately means lower RMSE and MAE on the 2025 holdout. Spearman ρ, in-sample R², and AIC are secondary. Team score is a check that uses the actual scoring total.

Unit is the team-season. Only scoring teams (five or more finishers) with a lag of 1 or 2 years.

Outcome: `state_place` (main), `state_score` (check).

Predictors come from the prior available Kenilworth championship, never the same race as the outcome:
- `lag_star_z`, `lag_depth_z`, `lag_pack_gap` (pack gap is exploratory on its own)
- controls: `log_enrollment`, `C(sector)` (charter as the reference)
- exploratory: `wcac`

Fit 2019 and 2021–2024. Evaluate 2025.

OLS with school-clustered standard errors. Ordered logit, wild cluster bootstrap (999), rolling-origin, permutation, and the within-team swap are extra checks.

Confirmatory: holdout RMSE/MAE for fifth-runner vs first-runner (and vs controls). Everything else is exploratory.

Drop 2020, non-5k, non-varsity, same-year features, lag gaps over 2, and grades outside 9–12 when grade is labeled.
