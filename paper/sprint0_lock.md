# Sprint 0 lock — DC boys XC

Locked 2026-08-15. Changes to H1/H2 go in `paper/hypothesis_log.md`.

## Population
- **Jurisdiction:** District of Columbia (DCSAA), not a classified state like MD/VA.
- **Gender:** Boys / men. Varsity 5,000 m championship race only.
- **Girls:** replication appendix later, not the main paper.
- **Unit of analysis:** team-season.
- **Championship:** one undivided DCSAA varsity boys race at **Kenilworth Park**. No 3A/4A. Max seven varsity runners; five finishers required to score ([2025 bulletin](https://assets-rst7.rschooltoday.com/rst7files/uploads/sites/801/2025/10/23133136/DCSAA-2025-XC-Bulletin.pdf)).

## Seasons and split
- **Seasons:** Kenilworth era **2016–2019 and 2021–2025**. Skip **2020** (COVID).
- **Fit:** 2017–2024 (2016 is used only to build lagged features for 2017).
- **Holdout:** 2025 (do not tune on it).
- **N strategy:** more years, not MD/VA. Girls remain appendix-only. Invitational team–meet rows are a **secondary** analysis when those files exist; the headline model uses **lagged Kenilworth** star/depth so predictors never use the same race as the outcome.

Meet index: `data/meets_championship.csv`.

## Hypotheses
**H1.** After controlling for 9–12 enrollment and public/private/charter status, a team’s **prior-year Kenilworth** **depth** (within-meet z-score of the 5th runner) predicts this year’s DCSAA boys team place better than **star power** (within-meet z-score of the 1st runner). Same-race #1/#5 times are never used as predictors.

**H2.** **WCAC membership** (stronger regular-season field) predicts residual DCSAA team place after the H1 model. A secondary invitational-field SOS is used if those results are cached.

## Why DC is a feature, not a bug
- **Census, not sample:** ~13 scoring boys teams per year × 9 Kenilworth seasons, with lags, is on the order of 80–110 team-seasons. Report uncertainty; skip flashy ML.
- **The real confounder is sector, not class:** Gonzaga, St. John’s, St. Albans, Sidwell vs DCPS/charter schools. Use `public_private` + enrollment instead of classification.
- **Same championship course** (Kenilworth) reduces championship-time incomparability; regular-season invitationals still need z-scores (often in MD/VA).

## Data sources
| Layer | Role | Source |
| --- | --- | --- |
| A | Gold team place/score | MileSplit raw championship results; M&D Timing 2025; DCSAA boys page |
| B | Pre-state features | Team calendars on [athletic.net](https://www.athletic.net/) and [dc.milesplit.com](https://dc.milesplit.com/); varsity 5k only |
| C | Controls | NCES CCD/ELSI (DCPS), PSS (privates), OSSE as backup |

Championship URLs are in `data/meets_championship.csv`. DCSAA: https://www.dcsaasports.com/boys-cross-country/

## Inclusion
- DCSAA member schools that ran the **varsity boys championship** 5k.
- Primary sample: teams with five finishers (scored). Incomplete teams kept only for the qualifier/descriptive appendix.
- Predictors use **only meets before that year’s championship date**.
- Drop non-5k or flag separately. Ignore JV, Varsity B, and middle school races.

## Ethics
Public varsity places and times only. No recruiting lists, addresses, grades, or SIS data. Prefer school-level aggregates in the released CSV; athlete names may stay in raw caches but are not required in the analysis file.

## Tools
Python 3, `requirements.txt` (pandas, statsmodels, scikit-learn, matplotlib). Folders: `data/raw`, `data/clean`, `notebooks`, `paper`.
