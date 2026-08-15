"""Build lagged Kenilworth panel and run H1/H2 models."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from src.parse_results import parse_file
from src.schools import load_school_lookup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "championships"
CLEAN = ROOT / "data" / "clean"
FIG = ROOT / "paper" / "figures"


def discover_raw() -> dict[int, Path]:
    found = {}
    if not RAW.exists():
        return found
    for p in RAW.glob("*.txt"):
        for token in p.stem.replace("-", "_").split("_"):
            if token.isdigit() and len(token) == 4:
                found[int(token)] = p
                break
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
            scored.append({"season": season, "school": school, "state_score": score})
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
    feats = team_features_from_individuals(individuals)
    posted = pd.concat(teams, ignore_index=True) if teams else pd.DataFrame()
    derived = derive_scores(individuals)
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
    panel["log_enrollment"] = np.log(panel["enrollment_9_12"].clip(lower=50))
    panel = panel.sort_values(["school", "season"])
    lag_cols = ["star_z", "depth_z", "pack_gap", "state_place", "state_score"]
    for col in lag_cols:
        panel[f"lag_{col}"] = panel.groupby("school")[col].shift(1)
    # 2021 should lag 2019 not 2020 (already true if 2020 absent)
    panel["fit_set"] = panel["season"].between(2017, 2024) & panel["lag_depth_z"].notna()
    panel["holdout"] = (panel["season"] == 2025) & panel["lag_depth_z"].notna()
    posted_keys = set(zip(posted["season"], posted["school"])) if not posted.empty else set()
    panel["score_source"] = panel.apply(
        lambda r: "posted_team_table" if (r["season"], r["school"]) in posted_keys else "reconstructed_from_individuals",
        axis=1,
    )
    panel_path = CLEAN / ("team_seasons.csv" if sex == "M" else "team_seasons_girls.csv")
    panel.to_csv(panel_path, index=False)
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
        elif season in (2017, 2018):
            note = "Archived file is junior varsity; varsity not parsed"
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
            {"rule": "race_type", "detail": "Junior varsity, Varsity B, and middle school events excluded"},
            {"rule": "scoring_squad", "detail": "Star/depth from the seven fastest recorded varsity times per school; extra finishers in mixed dumps ignored"},
            {"rule": "no_invitationals", "detail": "Invitational SOS not ingested; WCAC is only a coarse proxy"},
            {"rule": "five_finishers", "detail": "Regression requires five finishers so a fifth-runner z-score exists"},
            {"rule": "lag", "detail": "Estimation/holdout require a prior parsed championship for the same school"},
            {"rule": "2021_lag", "detail": "2021 uses 2019 as the prior championship because 2020 is omitted"},
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


def _wild_cluster_ci(formula: str, df: pd.DataFrame, term: str, rng: np.random.Generator, n_boot: int = 399) -> dict:
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


def run_models(panel: pd.DataFrame, *, result_stem: str = "model_results") -> dict:
    rng = np.random.default_rng(2025)
    fit = panel.loc[panel["fit_set"] & panel["n_finishers"].ge(5)].copy()
    hold = panel.loc[panel["holdout"] & panel["n_finishers"].ge(5)].copy()
    formulas = {
        "controls": "state_place ~ log_enrollment + C(sector)",
        "star": "state_place ~ log_enrollment + C(sector) + lag_star_z",
        "depth": "state_place ~ log_enrollment + C(sector) + lag_depth_z",
        "pack_gap": "state_place ~ log_enrollment + C(sector) + lag_pack_gap",
        "star_gap": "state_place ~ log_enrollment + C(sector) + lag_star_z + lag_pack_gap",
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
    aics = {k: results[k]["aic"] for k in ("controls", "star", "depth", "pack_gap", "star_gap", "both", "wcac")}
    best = min(aics.values())
    results["delta_aic"] = {k: float(v - best) for k, v in aics.items()}
    score_aics = {k: results[k]["aic"] for k in ("score_controls", "score_star", "score_depth", "score_pack_gap", "score_both")}
    sbest = min(score_aics.values())
    results["score_delta_aic"] = {k: float(v - sbest) for k, v in score_aics.items()}
    results["n_clusters"] = int(fit["school"].nunique())
    results["seasons_fit"] = sorted(int(s) for s in fit["season"].unique())
    results["star_depth_corr"] = float(fit["lag_star_z"].corr(fit["lag_depth_z"]))

    results["holdout_by_model"] = {}
    if len(hold):
        for name in ("controls", "star", "depth", "pack_gap", "star_gap", "both", "wcac"):
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
            for _ in range(1000):
                b = rng.choice(idx, size=len(idx), replace=True)
                err = y[b] - p[b]
                boots.append(np.sqrt(np.mean(err**2)))
            results["holdout_rmse_bootstrap"] = {
                "mean": float(np.mean(boots)),
                "ci_low": float(np.percentile(boots, 2.5)),
                "ci_high": float(np.percentile(boots, 97.5)),
            }
        if "depth" in results["holdout_by_model"]:
            results["holdout"] = results["holdout_by_model"]["depth"]

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

    obs_r2 = models["depth"].rsquared
    perm_r2 = []
    for _ in range(199):
        tmp = fit.copy()
        tmp["lag_depth_z"] = rng.permutation(tmp["lag_depth_z"].to_numpy())
        perm_r2.append(_fit_cluster("state_place ~ log_enrollment + C(sector) + lag_depth_z", tmp).rsquared)
    results["permutation_depth_r2"] = {
        "observed": float(obs_r2),
        "p": float((np.sum(np.array(perm_r2) >= obs_r2) + 1) / (len(perm_r2) + 1)),
    }
    obs_delta = models["depth"].rsquared - models["star"].rsquared
    swap_delta = []
    for _ in range(199):
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
        "p": float((np.sum(np.array(swap_delta) >= obs_delta) + 1) / (len(swap_delta) + 1)),
    }

    (CLEAN / f"{result_stem}.json").write_text(json.dumps(results, indent=2))
    lines = [
        "# Confirmatory results (school-clustered SEs)\n",
        f"Clusters: {results['n_clusters']}; seasons: {results['seasons_fit']}; star-depth r={results['star_depth_corr']:.3f}\n",
        f"Delta AIC vs best: {results['delta_aic']}\n",
        f"Holdout by model: {results.get('holdout_by_model')}\n",
        f"LOO school depth coef: {results['loo_school_depth_coef']}\n",
        f"LOO season RMSE: {results['loo_season_rmse']}\n",
        f"Permutation: {results['permutation_depth_r2']} {results['permutation_depth_minus_star_r2']}\n",
    ]
    for name, m in models.items():
        lines.append(f"## {name} (N={int(m.nobs)}, R^2={m.rsquared:.3f})\n")
        lines.append(m.summary().as_text())
        lines.append("\n")
    if result_stem == "model_results":
        (ROOT / "paper" / "results.md").write_text("\n".join(lines), encoding="utf-8")
    return {"models": models, "fit": fit, "hold": hold, "metrics": results}


def figures(panel: pd.DataFrame, fit: pd.DataFrame) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    d = fit.dropna(subset=["lag_depth_z", "state_place"])
    fig, ax = plt.subplots(figsize=(6, 4))
    for sector, g in d.groupby("sector"):
        ax.scatter(g["lag_pack_gap"], g["state_place"], label=sector, alpha=0.75)
    ax.set_xlabel("Lagged pack gap (5th z − 1st z)")
    ax.set_ylabel("DCSAA team place (lower is better)")
    ax.invert_yaxis()
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "pack_gap_vs_place.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(d["lag_star_z"], d["state_place"], label="lag star z", alpha=0.7)
    ax.scatter(d["lag_depth_z"], d["state_place"], label="lag depth z", alpha=0.7, marker="s")
    ax.set_xlabel("Within-meet z (lower = faster)")
    ax.set_ylabel("DCSAA team place")
    ax.invert_yaxis()
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "star_depth_vs_place.png", dpi=150)
    plt.close(fig)

    counts = panel.groupby("season")["school"].nunique()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(counts.index.astype(str), counts.values)
    ax.set_ylabel("Teams in parsed championship file")
    fig.tight_layout()
    fig.savefig(FIG / "teams_by_season.png", dpi=150)
    plt.close(fig)


def main() -> None:
    panel = build_panel("M")
    out = run_models(panel, result_stem="model_results")
    figures(panel, out["fit"])
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
