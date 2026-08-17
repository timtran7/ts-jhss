# DCSAA boys cross country

I looked at whether last championship's fifth runner or first runner does a better job of predicting next DCSAA boys team place at Kenilworth.

The paper is `paper/Tran_Timothy.docx` (Oxford Journal of Student Scholarship). To rebuild numbers and the Word file:

```bash
pip install -r requirements.txt
set PYTHONPATH=.
python -m src.run_pipeline
python -m src.build_ojss
```

On Mac/Linux, use `export PYTHONPATH=.` instead of `set`.

The test I locked in is 2025 holdout RMSE/MAE for team place, after enrollment and sector. Fit years are 2019 and 2021–2024. See `paper/protocol.md` if you need the exact rules.
