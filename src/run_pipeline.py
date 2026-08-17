"""Build lagged Kenilworth panel and run H1/H2 models."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.miscmodels.ordinal_model import OrderedModel

from src.parse_results import parse_file, _is_jv_only_archive
from src.schools import load_school_lookup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "championships"
CLEAN = ROOT / "data" / "clean"
ENROLL_YEAR = ROOT / "data" / "enrollment_by_year.csv"


def discover_raw() -> dict[int, Path]:
    found = {}
    if not RAW.exists():
        return found

    def _consider(p: Path, overwrite: bool) -> None:
        text = p.read_text(encoding="utf-8", errors="ignore")
        if _is_jv_only_archive(text):
            return
        for token in p.stem.replace("-", "_").split("_"):
            if token.isdigit() and len(token) == 4:
                year = int(token)
                if overwrite or year not in found:
                    found[year] = p
                break

    # Prefer canonical dcsaa_YYYY.txt; ignore auxiliary dumps (pacers_*, etc.).
    for p in sorted(RAW.glob("dcsaa_*.txt")):
        _consider(p, overwrite=True)
    for p in sorted(RAW.glob("*.txt")):
        if p.name.startswith("dcsaa_"):
            continue
        _consider(p, overwrite=False)
    return found


def team_features_from_individuals(ind: pd.DataFrame) -> pd.DataFrame:
    if ind.empty:
        return pd.DataFrame()
    g = ind.groupby(["season", "school"], sort=False)
    rows = []
    for (season, school), grp in g:
        n_raw = len(grp)
        grp = grp.sort_values("time_sec").head(7)
        times = grp["time_sec"].to_numpy()
        meet_mean = ind.loc[ind["season"] == season, "time_sec"].mean()
        meet_std = ind.loc[ind["season"] == season, "time_sec"].std(ddof=0) or 1.0
        z = (times - meet_mean) / meet_std
        n = len(times)
        rows.append(
            {
                "season": season,
                "school": school,
                "n_finishers_raw": n_raw,
                "n_finishers": n,
                "star_z": float(z[0]) if n else np.nan,
                "depth_z": float(z[4]) if n >= 5 else np.nan,
                "pack_gap": float(z[4] - z[0]) if n >= 5 else np.nan,
                "star_time": float(times[0]) if n else np.nan,
                "depth_time": float(times[4]) if n >= 5 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def derive_scores(ind: pd.DataFrame) -> pd.DataFrame:
    """Recompute team scores if MileSplit team table missing."""
    if ind.empty:
        return pd.DataFrame()
    out = []
    for season, sdf in ind.groupby("season"):
        sdf = sdf.sort_values("place")
        scored = []
        for school, grp in sdf.groupby("school"):
            grp = grp.sort_values("place").head(7)
            if len(grp) < 5:
                continue
            score = int(grp["place"].iloc[:5].sum())
            row = {"season": season, "school": school, "state_score": score}
            if "sex" in grp.columns and grp["sex"].notna().any():
                row["sex"] = grp["sex"].dropna().iloc[0]
            scored.append(row)
        t = pd.DataFrame(scored).sort_values("state_score")
        t["state_place"] = range(1, len(t) + 1)
        out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def build_panel(sex: str = "M") -> pd.DataFrame:
    schools, alias_map = load_school_lookup(str(ROOT / "data" / "schools.csv"))
    raw_map = discover_raw()
    inds = []
    teams = []
    for season, path in sorted(raw_map.items()):
        ind, team = parse_file(path, season, alias_map, sex=sex)
        if not ind.empty:
            inds.append(ind)
        if not team.empty:
            teams.append(team)
    individuals = pd.concat(inds, ignore_index=True) if inds else pd.DataFrame()
    CLEAN.mkdir(parents=True, exist_ok=True)
    if not individuals.empty:
        out_ind = CLEAN / ("championship_individuals.csv" if sex == "M" else "championship_individuals_girls.csv")
        individuals.to_csv(out_ind, index=False)
        if sex == "M":
            pd.DataFrame(_field_stats(individuals)).to_csv(CLEAN / "field_stats_by_season.csv", index=False)
    feats = team_features_from_individuals(individuals)
    posted = pd.concat(teams, ignore_index=True) if teams else pd.DataFrame()
    derived = derive_scores(individuals)
    if sex == "M":
        (CLEAN / "score_reconciliation.json").write_text(
            json.dumps(_score_reconciliation(posted, derived), indent=2), encoding="utf-8"
        )
    if not posted.empty:
        panel = posted.merge(feats, on=["season", "school"], how="left")
        extra = derived.merge(feats, on=["season", "school"], how="left") if not derived.empty else pd.DataFrame()
        if not extra.empty:
            have = set(zip(panel["season"], panel["school"]))
            extra = extra[~extra.apply(lambda r: (r["season"], r["school"]) in have, axis=1)]
            panel = pd.concat([panel, extra], ignore_index=True)
    else:
        panel = derived.merge(feats, on=["season", "school"], how="left")
    panel = panel.merge(schools, left_on="school", right_on="canonical", how="left")
    unmapped = sorted({s for s in panel.loc[panel["sector"].isna(), "school"].dropna()})
    (CLEAN / "unmapped_schools.json").write_text(json.dumps(unmapped, indent=2))
    panel = panel.loc[panel["sector"].notna()].copy()
    # Prefer year-varying enrollment when available; else static schools.csv estimate.
    panel["enrollment_source"] = "static_schools_csv"
    if ENROLL_YEAR.exists():
        ey = pd.read_csv(ENROLL_YEAR)
        panel = panel.merge(
            ey.rename(columns={"enrollment_9_12": "enrollment_year", "source": "enrollment_year_source"}),
            left_on=["school", "season"],
            right_on=["school", "season"],
            how="left",
        )
        use = panel["enrollment_year"].notna()
        panel.loc[use, "enrollment_9_12"] = panel.loc[use, "enrollment_year"]
        panel.loc[use, "enrollment_source"] = panel.loc[use, "enrollment_year_source"].fillna("enrollment_by_year")
        panel = panel.drop(columns=["enrollment_year", "enrollment_year_source"], errors="ignore")
    panel["log_enrollment"] = np.log(panel["enrollment_9_12"].clip(lower=50))
    panel = panel.sort_values(["school", "season"])
    panel["prev_season"] = panel.groupby("school")["season"].shift(1)
    panel["lag_gap_years"] = panel["season"] - panel["prev_season"]
    lag_cols = ["star_z", "depth_z", "pack_gap", "state_place", "state_score", "star_time", "depth_time"]
    for col in lag_cols:
        if col in panel.columns:
            panel[f"lag_{col}"] = panel.groupby("school")[col].shift(1)
    # Boys: fit through 2024, hold out 2025. Girls: no 2025 panel; hold out 2024.
    # Cap lag gap at 2 years (allows 2019→2021 after omitted 2020; drops longer skips).
    holdout_year = 2025 if sex == "M" else 2024
    max_lag_gap = 2
    eligible_lag = panel["lag_depth_z"].notna() & panel["lag_gap_years"].between(1, max_lag_gap)
    scoring = panel["n_finishers"].ge(5)
    panel["fit_set"] = (
        panel["season"].between(2017, 2024)
        & (panel["season"] != holdout_year)
        & eligible_lag
        & scoring
    )
    panel["holdout"] = (panel["season"] == holdout_year) & eligible_lag & scoring
    posted_keys = set(zip(posted["season"], posted["school"])) if not posted.empty else set()
    panel["score_source"] = panel.apply(
        lambda r: "posted_team_table" if (r["season"], r["school"]) in posted_keys else "reconstructed_from_individuals",
        axis=1,
    )
    if "sex" not in panel.columns:
        panel["sex"] = sex
    else:
        panel["sex"] = panel["sex"].fillna(sex)
    panel_path = CLEAN / ("team_seasons.csv" if sex == "M" else "team_seasons_girls.csv")
    panel.to_csv(panel_path, index=False)
    if sex == "M":
        (CLEAN / "inclusion_summary.json").write_text(
            json.dumps(_inclusion_summary(panel), indent=2), encoding="utf-8"
        )
    if sex != "M":
        return panel
    audit_rows = []
    for season, path in sorted(raw_map.items()):
        n_ind = int((individuals["season"] == season).sum()) if not individuals.empty else 0
        n_sch = int(panel.loc[panel["season"] == season, "school"].nunique())
        n_score = int(((panel["season"] == season) & panel["n_finishers"].ge(5)).sum())
        n_fit = int(((panel["season"] == season) & panel["fit_set"]).sum())
        n_hold = int(((panel["season"] == season) & panel["holdout"]).sum())
        note = ""
        if season == 2016:
            note = "Individual times present without school names; excluded"
        elif season == 2018:
            note = "Pacers Running varsity team-standings dump (RunWashington)"
        elif season == 2020:
            note = "Omitted (no championship)"
        audit_rows.append(
            {
                "season": season,
                "source_file": path.name,
                "individual_finishers_parsed": n_ind,
                "schools_in_panel": n_sch,
                "scoring_teams_ge5": n_score,
                "estimation_rows": n_fit,
                "holdout_rows": n_hold,
                "notes": note,
            }
        )
    pd.DataFrame(audit_rows).to_csv(CLEAN / "season_audit.csv", index=False)
    if 2020 not in raw_map:
        extra = pd.DataFrame(
            [
                {
                    "season": 2020,
                    "source_file": "",
                    "individual_finishers_parsed": 0,
                    "schools_in_panel": 0,
                    "scoring_teams_ge5": 0,
                    "estimation_rows": 0,
                    "holdout_rows": 0,
                    "notes": "Omitted; no championship",
                }
            ]
        )
        audit = pd.read_csv(CLEAN / "season_audit.csv")
        pd.concat([audit, extra], ignore_index=True).sort_values("season").to_csv(
            CLEAN / "season_audit.csv", index=False
        )
    excl = pd.DataFrame(
        [
            {"rule": "time_window", "detail": "Finish times outside 14–45 min dropped as incomplete or not 5 km"},
            {"rule": "race_type", "detail": "Varsity A 5 km championship finishers only"},
            {"rule": "grade", "detail": "When grade is labeled, only grades 9–12 enter meet z-scores and squad features"},
            {"rule": "scoring_squad", "detail": "Star/depth from the seven fastest recorded varsity times per school; extra finishers in mixed dumps ignored"},
            {"rule": "no_invitationals", "detail": "Invitational SOS not ingested; WCAC is only a coarse proxy"},
            {"rule": "five_finishers", "detail": "Estimation/holdout require five finishers so a fifth-runner z-score exists"},
            {"rule": "lag", "detail": "Estimation/holdout require a prior parsed championship for the same school"},
            {"rule": "lag_gap", "detail": "Lag gap capped at 2 years (permits 2019→2021 after omitted 2020; longer skips excluded)"},
            {"rule": "2021_lag", "detail": "2021 uses 2019 as the prior championship because 2020 is omitted"},
            {"rule": "2019_lag", "detail": "2019 can lag 2018 when Pacers varsity team standings are present"},
            {"rule": "girls_holdout", "detail": "Girls reserve 2024 as temporal holdout because 2025 girls files are not in the panel"},
            {"rule": "enrollment", "detail": "Public DCPS schools use year-varying audit counts when available; private/charter use static schools.csv unless overridden"},
            {"rule": "unmapped_schools", "detail": "Names not in data/schools.csv dropped; see unmapped_schools.json"},
            {"rule": "ties", "detail": "Posted team place used when available; reconstructed ranks break remaining ties by score then school name"},
        ]
    )
    excl.to_csv(CLEAN / "exclusion_log.csv", index=False)
    return panel


def _dump_fit(m) -> dict:
    ci = m.conf_int()
    return {
        "n": int(m.nobs),
        "rsquared": float(m.rsquared),
        "rsquared_adj": float(m.rsquared_adj),
        "aic": float(m.aic),
        "params": {k: float(v) for k, v in m.params.items()},
        "pvalues": {k: float(v) for k, v in m.pvalues.items()},
        "bse": {k: float(v) for k, v in m.bse.items()},
        "ci_low": {k: float(ci.loc[k, 0]) for k in m.params.index},
        "ci_high": {k: float(ci.loc[k, 1]) for k in m.params.index},
    }


def _fit_cluster(formula: str, df: pd.DataFrame):
    return smf.ols(formula, data=df).fit(
        cov_type="cluster",
        cov_kwds={"groups": df["school"], "use_correction": True},
    )


def _wild_cluster_ci(formula: str, df: pd.DataFrame, term: str, rng: np.random.Generator, n_boot: int = 999) -> dict:
    m0 = smf.ols(formula, data=df).fit()
    outcome = formula.split("~")[0].strip()
    yhat = m0.fittedvalues.to_numpy()
    resid = m0.resid.to_numpy()
    groups = df["school"].to_numpy()
    uniq = list(df["school"].unique())
    coefs = []
    for _ in range(n_boot):
        signs = {g: float(rng.choice([-1.0, 1.0])) for g in uniq}
        tmp = df.copy()
        tmp[outcome] = yhat + resid * np.array([signs[g] for g in groups])
        try:
            mb = smf.ols(formula, data=tmp).fit()
            coefs.append(float(mb.params[term]))
        except Exception:
            continue
    arr = np.array(coefs)
    obs = float(m0.params[term])
    return {
        "term": term,
        "observed": obs,
        "n_boot": int(len(arr)),
        "ci_low": float(np.percentile(arr, 2.5)),
        "ci_high": float(np.percentile(arr, 97.5)),
        "excludes_zero": bool(np.percentile(arr, 2.5) > 0 or np.percentile(arr, 97.5) < 0),
        "method": "wild_cluster_residual_sign_flip",
    }


def _loo_predict_rmse(formula: str, df: pd.DataFrame, outcome: str) -> dict:
    y_true = []
    y_pred = []
    by_school = {}
    for sch in df["school"].unique():
        tr = df.loc[df["school"] != sch]
        te = df.loc[df["school"] == sch]
        if tr["school"].nunique() < 3 or te.empty:
            continue
        m = _fit_cluster(formula, tr)
        try:
            pred = m.predict(te)
        except Exception:
            continue
        y_true.extend(te[outcome].tolist())
        y_pred.extend(pred.tolist())
        err = te[outcome].to_numpy() - pred.to_numpy()
        by_school[str(sch)] = float(np.sqrt(np.mean(err**2)))
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    if len(y_true) == 0:
        return {"n": 0, "rmse": None, "mae": None, "by_school": by_school}
    return {
        "n": int(len(y_true)),
        "rmse": float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
        "mae": float(np.mean(np.abs(y_true - y_pred))),
        "by_school": by_school,
    }


def _pred_metrics(y: pd.Series, pred: pd.Series) -> dict:
    err = y.to_numpy() - pred.to_numpy()
    return {
        "n": int(len(y)),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mae": float(np.mean(np.abs(err))),
        "spearman": float(pd.Series(y).corr(pd.Series(pred), method="spearman")),
    }


def _software_versions() -> dict:
    import sys

    import matplotlib
    import numpy
    import pandas
    import statsmodels

    return {
        "python": sys.version.split()[0],
        "pandas": pandas.__version__,
        "numpy": numpy.__version__,
        "statsmodels": statsmodels.__version__,
        "matplotlib": matplotlib.__version__,
        "seed": 2025,
    }


def _vif_pair(df: pd.DataFrame, a: str, b: str, controls: str) -> dict:
    """VIF for two collinear predictors given controls (R² from auxiliary OLS)."""
    out = {}
    for term, other in ((a, b), (b, a)):
        try:
            m = smf.ols(f"{term} ~ {controls} + {other}", data=df).fit()
            r2 = float(m.rsquared)
            out[term] = {"r_squared_aux": r2, "vif": float(1.0 / max(1e-12, 1.0 - r2))}
        except Exception as e:
            out[term] = {"error": str(e)}
    return out


def _partial_corr(df: pd.DataFrame, x: str, y: str) -> float | None:
    """Partial correlation of x and y after log_enrollment and sector dummies."""
    try:
        d = df[[x, y, "log_enrollment", "sector"]].copy()
        d = pd.get_dummies(d, columns=["sector"], drop_first=True, dtype=float)
        ctrl = [c for c in d.columns if c not in (x, y)]
        rx = smf.ols(f"{x} ~ " + " + ".join(ctrl), data=d).fit().resid
        ry = smf.ols(f"{y} ~ " + " + ".join(ctrl), data=d).fit().resid
        return float(pd.Series(rx).corr(pd.Series(ry)))
    except Exception:
        return None


def _paired_rmse_diff(
    y: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray, rng: np.random.Generator, n_boot: int = 2000
) -> dict:
    """Bootstrap CI for RMSE(a) − RMSE(b) with paired holdout rows."""
    idx = np.arange(len(y))

    def rmse(p):
        return float(np.sqrt(np.mean((y - p) ** 2)))

    obs = rmse(pred_a) - rmse(pred_b)
    diffs = []
    for _ in range(n_boot):
        b = rng.choice(idx, size=len(idx), replace=True)
        diffs.append(rmse(pred_a[b]) - rmse(pred_b[b]))
    arr = np.asarray(diffs, dtype=float)
    return {
        "observed": obs,
        "ci_low": float(np.percentile(arr, 2.5)),
        "ci_high": float(np.percentile(arr, 97.5)),
        "n_boot": int(len(arr)),
        "note": "negative favors model a (lower RMSE)",
    }


def _rolling_origin_place(panel: pd.DataFrame) -> dict:
    """Expanding-window train → predict each later season (temporal transportability)."""
    use = panel.loc[panel["fit_set"] | panel["holdout"]].copy()
    # Freeze sector levels so predict() works when a training window lacks a sector.
    use["sector"] = pd.Categorical(use["sector"], categories=sorted(use["sector"].dropna().unique()))
    seasons = sorted(int(s) for s in use["season"].unique())
    rows = []
    for test_year in seasons:
        train = use.loc[use["season"] < test_year].copy()
        test = use.loc[use["season"] == test_year].copy()
        if len(train) < 12 or train["school"].nunique() < 4 or len(test) < 3:
            continue
        if train["sector"].nunique() < 2:
            continue
        try:
            m_star = _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_star_z", train)
            m_depth = _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_z", train)
            m_ctrl = _fit_cluster("state_place ~ log_enrollment + C(sector)", train)
            rows.append(
                {
                    "test_year": test_year,
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    "rmse_controls": _pred_metrics(test["state_place"], m_ctrl.predict(test))["rmse"],
                    "rmse_star": _pred_metrics(test["state_place"], m_star.predict(test))["rmse"],
                    "rmse_depth": _pred_metrics(test["state_place"], m_depth.predict(test))["rmse"],
                }
            )
        except Exception:
            continue
    if not rows:
        return {"years": []}
    tab = pd.DataFrame(rows)
    return {
        "years": rows,
        "mean_rmse_controls": float(tab["rmse_controls"].mean()),
        "mean_rmse_star": float(tab["rmse_star"].mean()),
        "mean_rmse_depth": float(tab["rmse_depth"].mean()),
        "depth_beats_star_years": int((tab["rmse_depth"] < tab["rmse_star"]).sum()),
        "n_years": int(len(tab)),
    }


def _score_reconciliation(posted: pd.DataFrame, derived: pd.DataFrame) -> dict:
    if posted.empty or derived.empty:
        return {"n_overlap": 0}
    a = posted.rename(columns={"state_place": "posted_place", "state_score": "posted_score"})
    b = derived.rename(columns={"state_place": "recon_place", "state_score": "recon_score"})
    m = a.merge(b, on=["season", "school"], how="inner")
    if m.empty:
        return {"n_overlap": 0}
    score_match = (m["posted_score"] == m["recon_score"]).mean()
    place_match = (m["posted_place"] == m["recon_place"]).mean()
    return {
        "n_overlap": int(len(m)),
        "score_exact_match_rate": float(score_match),
        "place_exact_match_rate": float(place_match),
        "mean_abs_score_diff": float((m["posted_score"] - m["recon_score"]).abs().mean()),
        "mean_abs_place_diff": float((m["posted_place"] - m["recon_place"]).abs().mean()),
    }


def _inclusion_summary(panel: pd.DataFrame) -> dict:
    scoring = panel.loc[panel["n_finishers"].ge(5)].copy()
    analytic = scoring.loc[scoring["fit_set"] | scoring["holdout"]].copy()
    excluded = scoring.loc[~(scoring["fit_set"] | scoring["holdout"])].copy()

    def _pack(df: pd.DataFrame) -> dict:
        if df.empty:
            return {"n": 0}
        return {
            "n": int(len(df)),
            "n_schools": int(df["school"].nunique()),
            "sector_counts": {str(k): int(v) for k, v in df["sector"].value_counts().items()},
            "mean_enrollment": float(df["enrollment_9_12"].mean()),
            "mean_place": float(df["state_place"].mean()) if "state_place" in df else None,
        }

    return {"scoring_teams": _pack(scoring), "analytic": _pack(analytic), "excluded_scoring": _pack(excluded)}


def _field_stats(individuals: pd.DataFrame) -> list[dict]:
    if individuals.empty:
        return []
    rows = []
    for season, g in individuals.groupby("season"):
        rows.append(
            {
                "season": int(season),
                "n_finishers": int(len(g)),
                "mean_time_sec": float(g["time_sec"].mean()),
                "sd_time_sec": float(g["time_sec"].std(ddof=0)),
                "n_schools": int(g["school"].nunique()),
            }
        )
    return rows


def run_models(panel: pd.DataFrame, *, result_stem: str = "model_results") -> dict:
    rng = np.random.default_rng(2025)
    fit = panel.loc[panel["fit_set"]].copy()
    hold = panel.loc[panel["holdout"]].copy()
    formulas = {
        "controls": "state_place ~ log_enrollment + C(sector)",
        "star": "state_place ~ log_enrollment + C(sector) + lag_star_z",
        "depth": "state_place ~ log_enrollment + C(sector) + lag_depth_z",
        "pack_gap": "state_place ~ log_enrollment + C(sector) + lag_pack_gap",
        "both": "state_place ~ log_enrollment + C(sector) + lag_star_z + lag_depth_z",
        "wcac": "state_place ~ log_enrollment + C(sector) + lag_star_z + lag_depth_z + wcac",
        "score_controls": "state_score ~ log_enrollment + C(sector)",
        "score_star": "state_score ~ log_enrollment + C(sector) + lag_star_z",
        "score_depth": "state_score ~ log_enrollment + C(sector) + lag_depth_z",
        "score_pack_gap": "state_score ~ log_enrollment + C(sector) + lag_pack_gap",
        "score_both": "state_score ~ log_enrollment + C(sector) + lag_star_z + lag_depth_z",
    }
    models = {name: _fit_cluster(formula, fit) for name, formula in formulas.items()}
    results = {name: _dump_fit(m) for name, m in models.items()}
    aics = {k: results[k]["aic"] for k in ("controls", "star", "depth", "pack_gap", "both", "wcac")}
    best = min(aics.values())
    results["delta_aic"] = {k: float(v - best) for k, v in aics.items()}
    score_aics = {k: results[k]["aic"] for k in ("score_controls", "score_star", "score_depth", "score_pack_gap", "score_both")}
    sbest = min(score_aics.values())
    results["score_delta_aic"] = {k: float(v - sbest) for k, v in score_aics.items()}
    results["software"] = _software_versions()
    results["confirmatory_estimand"] = {
        "hypothesis": (
            "Among schools with an eligible prior championship result, prior fifth-runner relative time "
            "(within-meet z; higher = slower) predicts next championship team place more accurately than "
            "prior first-runner relative time after adjustment for log enrollment and school sector."
        ),
        "primary_outcome": "state_place",
        "primary_comparison": "holdout_rmse_and_mae_depth_vs_star_and_controls",
        "secondary": ["in_sample_r2", "aic", "state_score", "spearman"],
        "exploratory": ["wcac", "pack_gap", "ordered_logit", "girls_panel", "sensitivities"],
    }
    results["n_clusters"] = int(fit["school"].nunique())
    results["seasons_fit"] = sorted(int(s) for s in fit["season"].unique())
    results["star_depth_corr"] = float(fit["lag_star_z"].corr(fit["lag_depth_z"]))
    results["partial_corr_star_depth"] = _partial_corr(fit, "lag_star_z", "lag_depth_z")
    results["vif_joint"] = _vif_pair(fit, "lag_star_z", "lag_depth_z", "log_enrollment + C(sector)")
    if "lag_gap_years" in fit.columns:
        results["lag_gap_counts"] = {str(int(k)): int(v) for k, v in fit["lag_gap_years"].value_counts().sort_index().items()}

    holdout_year = int(hold["season"].iloc[0]) if len(hold) else None
    if holdout_year is not None:
        scoring_hold_year = int(((panel["season"] == holdout_year) & panel["n_finishers"].ge(5)).sum())
        results["holdout_coverage"] = {
            "year": holdout_year,
            "scoring_teams": scoring_hold_year,
            "with_usable_lag": int(len(hold)),
        }

    results["holdout_by_model"] = {}
    if len(hold):
        for name in ("controls", "star", "depth", "pack_gap", "both", "wcac"):
            try:
                pred = models[name].predict(hold)
            except Exception:
                results["holdout_by_model"][name] = {"n": int(len(hold)), "error": "predict_failed"}
                continue
            results["holdout_by_model"][name] = _pred_metrics(hold["state_place"], pred)
        results["holdout_score_by_model"] = {}
        for name in ("score_controls", "score_star", "score_depth", "score_pack_gap"):
            try:
                pred = models[name].predict(hold)
            except Exception:
                results["holdout_score_by_model"][name] = {"n": int(len(hold)), "error": "predict_failed"}
                continue
            results["holdout_score_by_model"][name] = _pred_metrics(hold["state_score"], pred)
        try:
            depth_pred = models["depth"].predict(hold)
        except Exception:
            depth_pred = None
        if depth_pred is not None:
            boots = []
            idx = np.arange(len(hold))
            y = hold["state_place"].to_numpy()
            p = depth_pred.to_numpy()
            for _ in range(2000):
                b = rng.choice(idx, size=len(idx), replace=True)
                err = y[b] - p[b]
                boots.append(np.sqrt(np.mean(err**2)))
            results["holdout_rmse_bootstrap"] = {
                "mean": float(np.mean(boots)),
                "ci_low": float(np.percentile(boots, 2.5)),
                "ci_high": float(np.percentile(boots, 97.5)),
                "n_boot": 2000,
            }
            try:
                star_pred = models["star"].predict(hold).to_numpy()
                ctrl_pred = models["controls"].predict(hold).to_numpy()
                results["holdout_rmse_diff"] = {
                    "depth_minus_star": _paired_rmse_diff(y, p, star_pred, rng),
                    "depth_minus_controls": _paired_rmse_diff(y, p, ctrl_pred, rng),
                }
            except Exception as e:
                results["holdout_rmse_diff"] = {"error": str(e)}
        if "depth" in results["holdout_by_model"]:
            results["holdout"] = results["holdout_by_model"]["depth"]

    results["rolling_origin"] = _rolling_origin_place(panel)
    if (CLEAN / "score_reconciliation.json").exists() and result_stem == "model_results":
        results["score_reconciliation"] = json.loads((CLEAN / "score_reconciliation.json").read_text(encoding="utf-8"))
    if (CLEAN / "inclusion_summary.json").exists() and result_stem == "model_results":
        results["inclusion_summary"] = json.loads((CLEAN / "inclusion_summary.json").read_text(encoding="utf-8"))
    if (CLEAN / "field_stats_by_season.csv").exists() and result_stem == "model_results":
        results["field_stats"] = pd.read_csv(CLEAN / "field_stats_by_season.csv").to_dict(orient="records")

    # Sensitivities: no enrollment; one-year lags only; raw prior times instead of z.
    try:
        results["sensitivity_no_enrollment"] = _dump_fit(
            _fit_cluster("state_place ~ C(sector) + lag_depth_z", fit)
        )
    except Exception as e:
        results["sensitivity_no_enrollment"] = {"error": str(e)}
    gap1 = fit.loc[fit["lag_gap_years"].eq(1)] if "lag_gap_years" in fit.columns else fit.iloc[0:0]
    if len(gap1) >= 12 and gap1["school"].nunique() >= 5:
        try:
            results["sensitivity_gap1_only"] = _dump_fit(
                _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_z", gap1)
            )
            results["sensitivity_gap1_only"]["n_rows"] = int(len(gap1))
            results["sensitivity_gap1_only"]["n_schools"] = int(gap1["school"].nunique())
        except Exception as e:
            results["sensitivity_gap1_only"] = {"error": str(e)}
    else:
        results["sensitivity_gap1_only"] = {"skipped": True, "n_rows": int(len(gap1))}
    if "lag_depth_time" in fit.columns and fit["lag_depth_time"].notna().sum() >= 12:
        try:
            results["sensitivity_raw_times"] = {
                "depth": _dump_fit(
                    _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_time", fit)
                ),
                "star": _dump_fit(
                    _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_star_time", fit)
                ),
            }
        except Exception as e:
            results["sensitivity_raw_times"] = {"error": str(e)}

    # Leave-one-school-out coefficients for depth
    depth_coefs = []
    for sch in fit["school"].unique():
        sub = fit.loc[fit["school"] != sch]
        if sub["school"].nunique() < 3:
            continue
        try:
            m = _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_z", sub)
            depth_coefs.append(float(m.params["lag_depth_z"]))
        except Exception:
            continue
    if depth_coefs:
        results["loo_school_depth_coef"] = {
            "n": len(depth_coefs),
            "mean": float(np.mean(depth_coefs)),
            "min": float(np.min(depth_coefs)),
            "max": float(np.max(depth_coefs)),
        }
    else:
        results["loo_school_depth_coef"] = {"n": 0}
    results["loo_school_place_rmse"] = _loo_predict_rmse(
        "state_place ~ log_enrollment + C(sector) + lag_depth_z", fit, "state_place"
    )
    results["loo_school_score_rmse"] = _loo_predict_rmse(
        "state_score ~ log_enrollment + C(sector) + lag_depth_z", fit, "state_score"
    )
    results["wild_cluster_depth"] = _wild_cluster_ci(
        "state_place ~ log_enrollment + C(sector) + lag_depth_z",
        fit,
        "lag_depth_z",
        rng,
    )
    results["wild_cluster_pack_gap"] = _wild_cluster_ci(
        "state_place ~ log_enrollment + C(sector) + lag_pack_gap",
        fit,
        "lag_pack_gap",
        rng,
    )

    season_rmse = {}
    for season in sorted(fit["season"].unique()):
        tr = fit.loc[fit["season"] != season]
        te = fit.loc[fit["season"] == season]
        try:
            m = _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_z", tr)
            pred = m.predict(te)
            season_rmse[str(int(season))] = _pred_metrics(te["state_place"], pred)["rmse"]
        except Exception:
            continue
    results["loo_season_rmse"] = season_rmse

    n_perm = 999
    obs_r2 = models["depth"].rsquared
    perm_r2 = []
    for _ in range(n_perm):
        tmp = fit.copy()
        tmp["lag_depth_z"] = rng.permutation(tmp["lag_depth_z"].to_numpy())
        perm_r2.append(_fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_z", tmp).rsquared)
    results["permutation_depth_r2"] = {
        "observed": float(obs_r2),
        "n_perm": n_perm,
        "p": float((np.sum(np.array(perm_r2) >= obs_r2) + 1) / (len(perm_r2) + 1)),
    }
    obs_delta = models["depth"].rsquared - models["star"].rsquared
    swap_delta = []
    for _ in range(n_perm):
        tmp = fit.copy()
        swap = rng.random(len(tmp)) < 0.5
        a = tmp["lag_star_z"].to_numpy().copy()
        b = tmp["lag_depth_z"].to_numpy().copy()
        a[swap], b[swap] = b[swap], a[swap]
        tmp["lag_star_z"], tmp["lag_depth_z"] = a, b
        r_star = _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_star_z", tmp).rsquared
        r_dep = _fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_z", tmp).rsquared
        swap_delta.append(r_dep - r_star)
    results["permutation_depth_minus_star_r2"] = {
        "observed": float(obs_delta),
        "n_perm": n_perm,
        "p": float((np.sum(np.array(swap_delta) >= obs_delta) + 1) / (len(swap_delta) + 1)),
    }

    # Ordered logit on place (robustness to OLS-on-ranks approximation).
    results["ordered_logit"] = {}
    for name, rhs in {
        "controls": "log_enrollment + C(sector)",
        "star": "log_enrollment + C(sector) + lag_star_z",
        "depth": "log_enrollment + C(sector) + lag_depth_z",
        "pack_gap": "log_enrollment + C(sector) + lag_pack_gap",
        "both": "log_enrollment + C(sector) + lag_star_z + lag_depth_z",
    }.items():
        try:
            om = OrderedModel.from_formula(
                f"state_place ~ {rhs}",
                data=fit.assign(state_place=fit["state_place"].astype(int)),
                distr="logit",
            )
            res = om.fit(method="bfgs", disp=False, maxiter=500)
            params = {k: float(v) for k, v in res.params.items() if not str(k).startswith("state_place")}
            pvals = {k: float(v) for k, v in res.pvalues.items() if k in params}
            results["ordered_logit"][name] = {
                "n": int(res.nobs),
                "llf": float(res.llf),
                "aic": float(res.aic),
                "params": params,
                "pvalues": pvals,
            }
        except Exception as e:
            results["ordered_logit"][name] = {"error": str(e)}
    if results["ordered_logit"]:
        aics = {k: v["aic"] for k, v in results["ordered_logit"].items() if "aic" in v}
        if aics:
            best = min(aics.values())
            results["ordered_logit_delta_aic"] = {k: float(v - best) for k, v in aics.items()}

    (CLEAN / f"{result_stem}.json").write_text(json.dumps(results, indent=2))
    return {"models": models, "fit": fit, "hold": hold, "metrics": results}


def main() -> None:
    panel = build_panel("M")
    out = run_models(panel, result_stem="model_results")
    print("boys", panel.groupby("season").size().to_dict())
    print("fit N", out["fit"].shape[0], "hold N", out["hold"].shape[0])
    girls = build_panel("F")
    if not girls.empty and girls["fit_set"].sum() >= 8:
        gout = run_models(girls, result_stem="model_results_girls")
        print("girls fit N", gout["fit"].shape[0], "hold N", gout["hold"].shape[0])
        print("girls depth R2", gout["metrics"]["depth"]["rsquared"])
    else:
        print("girls panel too small or empty", 0 if girls.empty else int(girls["fit_set"].sum()))


if __name__ == "__main__":
    main()
