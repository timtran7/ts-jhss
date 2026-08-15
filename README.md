# DC boys high school cross country

Journal-shaped empirical paper: **depth vs star** (and SOS) as predictors of **DCSAA** boys varsity team place.

Sprint 0 lock: [`paper/sprint0_lock.md`](paper/sprint0_lock.md). Protocol: [`paper/protocol.md`](paper/protocol.md). Manuscript for JHSS: [`paper/paper.md`](paper/paper.md) (original article format). Figure legends: [`paper/figure_legends.md`](paper/figure_legends.md). Submit as .docx, Times New Roman 12, 1.15 spacing, per [JHSS For Authors](https://jhss.scholasticahq.com/for-authors). Export `paper/figures/*.png` as separate JPEGs.

Rebuild tables and figures:

```bash
pip install -r requirements.txt
set PYTHONPATH=.
python -m src.run_pipeline
```

Kenilworth seasons with parsed varsity files in-repo: **2019, 2021, 2022, 2024, 2025** (skip 2020; 2016–2018/2023 not parseable yet). Fit uses lagged rows through 2024; **2025 holdout**.

- **H1:** Pre-championship 5th-runner within-meet z-score predicts DCSAA boys team place better than 1st-runner z-score, after enrollment and public/private/charter controls.
- **H2:** Pre-championship invitational field quality predicts residuals from H1.

Kenilworth-era seasons **2016–2019, 2021–2024** fit (with lags), **2025** holdout. Skip 2020. Gold championship results: `data/meets_championship.csv`. Run `python -m src.run_pipeline`.

GitHub sprints: [epic #1](https://github.com/timtran7/ts-jhss/issues/1).
