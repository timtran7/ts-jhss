"""Live audit and model numbers for the manuscript builder."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"


def _r(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def _pct(x: float) -> str:
    return f"{100 * x:.1f}"


def load_report() -> dict:
    m = json.loads((CLEAN / "model_results.json").read_text(encoding="utf-8"))
    g = json.loads((CLEAN / "model_results_girls.json").read_text(encoding="utf-8"))
    audit = pd.read_csv(CLEAN / "season_audit.csv")
    panel = pd.read_csv(CLEAN / "team_seasons.csv")
    fit = panel.loc[panel["fit_set"] & panel["n_finishers"].ge(5)].copy()
    n = int(m["controls"]["n"])
    n_schools = int(m["n_clusters"])
    corr = float(m["star_depth_corr"])
    hold_n = int(m["holdout"]["n"])

    def place_row(label: str, key: str, term: str, pretty: str | None = None) -> list[str]:
        d = m[key]
        da = float(m["delta_aic"][key])
        coef = d["params"][term]
        se = d["bse"][term]
        lo = d["ci_low"][term]
        hi = d["ci_high"][term]
        if pretty is None:
            focal = f"{_r(coef)} ({_r(se)})"
        else:
            focal = f"{pretty} {_r(coef)} ({_r(se)})"
        return [
            label,
            str(d["n"]),
            _r(d["rsquared"], 3),
            _r(d["rsquared_adj"], 3),
            _r(d["aic"], 1),
            _r(da, 1),
            focal,
            f"{_r(lo)}, {_r(hi)}",
        ]

    def hold_row(label: str, key: str) -> list[str]:
        h = m["holdout_by_model"][key]
        return [label, _r(h["rmse"]), _r(h["mae"]), _r(h["spearman"])]

    notes = {
        2016: "Times without school names",
        2018: "Pacers varsity dump",
        2019: "Lag from 2018",
        2020: "No championship",
        2021: "Lag from 2019",
        2022: "Lag and outcome",
        2023: "Collapsed HY-TEK recovered",
        2024: "Lag and outcome",
        2025: "Temporal holdout",
    }
    model_lags = fit.groupby("season").size().to_dict()
    audit_rows = []
    for _, r in audit.sort_values("season").iterrows():
        season = int(r["season"])
        src = str(r["source_file"]) if pd.notna(r["source_file"]) and str(r["source_file"]) else "—"
        fin = str(int(r["individual_finishers_parsed"]))
        score = str(int(r["scoring_teams_ge5"]))
        if season == 2025:
            lagged = f"{hold_n} holdout"
        elif season in model_lags:
            lagged = str(int(model_lags[season]))
        else:
            lagged = "0"
        audit_rows.append([str(season), src, fin, score, lagged, notes.get(season, "")])

    sector = fit["sector"].value_counts()
    wcac_n = int(fit["wcac"].sum()) if "wcac" in fit.columns else 0
    sample_rows = [
        ["Estimation team-seasons (N)", str(n)],
        ["Schools (clusters)", str(n_schools)],
        ["Seasons in estimation", "2019, 2021–2024"],
        [
            "Sector mix (private / public / charter)",
            f"{int(sector.get('private', 0))} / {int(sector.get('public', 0))} / {int(sector.get('charter', 0))}",
        ],
        ["WCAC school-seasons", f"{wcac_n} ({_pct(wcac_n / n)}%)"],
        [
            "Mean (SD) enrollment grades 9–12",
            f"{fit['enrollment_9_12'].mean():.0f} ({fit['enrollment_9_12'].std():.0f})",
        ],
        [
            "Mean (SD) prior first-runner z",
            f"{fit['lag_star_z'].mean():.2f} ({fit['lag_star_z'].std():.2f})",
        ],
        [
            "Mean (SD) prior fifth-runner z",
            f"{fit['lag_depth_z'].mean():.2f} ({fit['lag_depth_z'].std():.2f})",
        ],
        [
            "Mean (SD) next-year team place",
            f"{fit['state_place'].mean():.2f} ({fit['state_place'].std():.2f})",
        ],
        [
            "Mean (SD) next-year team score",
            f"{fit['state_score'].mean():.0f} ({fit['state_score'].std():.0f})",
        ],
        ["2025 holdout scoring teams", str(hold_n)],
    ]

    return {
        "m": m,
        "g": g,
        "n": n,
        "n_schools": n_schools,
        "corr": corr,
        "hold_n": hold_n,
        "audit_rows": audit_rows,
        "sample_rows": sample_rows,
        "place_table": [
            place_row("Controls", "controls", "C(sector)[T.private]", "Private"),
            place_row("+ first-runner z", "star", "lag_star_z"),
            place_row("+ fifth-runner z", "depth", "lag_depth_z"),
            place_row("+ pack gap", "pack_gap", "lag_pack_gap"),
            place_row("Both z-scores", "both", "lag_depth_z", "Fifth"),
            place_row("+ WCAC (exploratory)", "wcac", "wcac", "WCAC"),
        ],
        "hold_table": [
            hold_row("Controls (baseline)", "controls"),
            hold_row("First-runner z", "star"),
            hold_row("Pack gap", "pack_gap"),
            hold_row("Fifth-runner z", "depth"),
            hold_row("Both z-scores", "both"),
            hold_row("+ WCAC", "wcac"),
        ],
    }


def export_pdf(docx_path: Path, pdf_path: Path) -> Path:
    docx_path = docx_path.resolve()
    pdf_path = pdf_path.resolve()
    ps = (
        f"$word = New-Object -ComObject Word.Application; $word.Visible = $false; "
        f"$doc = $word.Documents.Open('{docx_path}'); "
        f"$pdf = '{pdf_path}'; $doc.SaveAs([ref]$pdf, [ref]17); "
        f"$doc.Close($false); $word.Quit()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    return pdf_path
