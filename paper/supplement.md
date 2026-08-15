# Supplement and reproducibility files

| File | Contents |
| --- | --- |
| `data/schools.csv` | Canonical names, sector, WCAC flag, enrollment, aliases |
| `data/meets_championship.csv` | Meet dates, MileSplit IDs, public result URLs |
| `data/clean/team_seasons.csv` | Analytic team-season panel |
| `data/clean/championship_individuals.csv` | Parsed varsity individual rows |
| `data/clean/season_audit.csv` | Finishers, scoring teams, lagged rows by year |
| `data/clean/exclusion_log.csv` | Inclusion and lag rules |
| `data/clean/unmapped_schools.json` | Names dropped for lack of a directory match |
| `data/clean/model_results.json` | Coefficients, CIs, holdout and sensitivity metrics |
| `src/run_pipeline.py` | Parse, lag, models, permutation and LOO checks |
| `src/build_manuscript.py` | Figures and Word manuscript |

Rebuild: `python -m src.run_pipeline` then `python -m src.build_manuscript`.
