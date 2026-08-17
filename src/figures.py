"""Publication figures for the manuscript."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
FIG = ROOT / "paper" / "figures"
SUPP = ROOT / "paper" / "supplement"

NAVY = "#1B365D"
TEAL = "#2A6F7F"
GOLD = "#C4A35A"
GRAY = "#4A4A4A"


def _style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": GRAY,
            "axes.labelcolor": "#222222",
            "xtick.color": "#222222",
            "ytick.color": "#222222",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def load_fit() -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = pd.read_csv(CLEAN / "team_seasons.csv")
    fit = panel.loc[panel["fit_set"]].copy()
    hold = panel.loc[panel["holdout"]].copy()
    return fit, hold


def write_analytic_sample(fit: pd.DataFrame) -> Path:
    SUPP.mkdir(parents=True, exist_ok=True)
    cols = [
        "season",
        "school",
        "prev_season",
        "lag_gap_years",
        "lag_star_z",
        "lag_depth_z",
        "lag_pack_gap",
        "enrollment_9_12",
        "enrollment_source",
        "sector",
        "wcac",
        "state_place",
        "state_score",
        "score_source",
    ]
    out = SUPP / "analytic_sample_boys.csv"
    keep = [c for c in cols if c in fit.columns]
    fit[keep].sort_values(["season", "state_place"]).to_csv(out, index=False)
    return out


def make_figures() -> dict[str, Path]:
    _style()
    FIG.mkdir(parents=True, exist_ok=True)
    fit, hold = load_fit()
    write_analytic_sample(fit)
    audit = pd.read_csv(CLEAN / "season_audit.csv")
    paths = {}
    colors = {"private": NAVY, "public": TEAL, "charter": GOLD}

    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    x = np.arange(len(audit))
    w = 0.27
    ax.bar(x - w, audit["individual_finishers_parsed"], width=w, color=GOLD, label="Individual finishers")
    ax.bar(x, audit["scoring_teams_ge5"], width=w, color=TEAL, label="Scoring teams (≥5)")
    ax.bar(x + w, audit["estimation_rows"] + audit["holdout_rows"], width=w, color=NAVY, label="Lagged rows")
    ax.set_xticks(x)
    ax.set_xticklabels(audit["season"].astype(int).astype(str))
    ax.set_xlabel("Championship season")
    ax.set_ylabel("Count (n)")
    ax.set_title("Season-by-season inclusion")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    p = FIG / "figure1_inclusion.jpg"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["f1"] = p

    d = fit.dropna(subset=["lag_depth_z", "state_place", "lag_pack_gap", "lag_star_z"])
    fig, ax = plt.subplots(figsize=(6.4, 4.5))
    for sector, g in d.groupby("sector"):
        ax.scatter(
            g["lag_pack_gap"],
            g["state_place"],
            c=colors.get(sector, GRAY),
            label=sector.title(),
            s=48,
            alpha=0.88,
            edgecolors="white",
            linewidths=0.5,
        )
    band = pd.DataFrame({"x": d["lag_pack_gap"], "y": d["state_place"]})
    m = smf.ols("y ~ x", band).fit()
    xs = np.linspace(band["x"].min(), band["x"].max(), 60)
    pr = m.get_prediction(pd.DataFrame({"x": xs})).summary_frame()
    ax.plot(xs, pr["mean"], color=GRAY, lw=1.4)
    ax.fill_between(xs, pr["mean_ci_lower"], pr["mean_ci_upper"], color=GRAY, alpha=0.18)
    ax.set_xlabel("Prior pack gap (fifth-runner z − first-runner z)")
    ax.set_ylabel("Next-year team place (1 = best)")
    ax.invert_yaxis()
    ax.legend(frameon=False, title="Sector")
    fig.tight_layout()
    p = FIG / "figure2_pack_gap.jpg"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["f2"] = p

    xlim = (
        min(d["lag_star_z"].min(), d["lag_depth_z"].min()) - 0.15,
        max(d["lag_star_z"].max(), d["lag_depth_z"].max()) + 0.15,
    )
    ylim = (d["state_place"].max() + 0.6, 0.4)
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 4.0), sharey=True)
    panels = [
        (axes[0], "lag_star_z", "Prior first-runner z", NAVY),
        (axes[1], "lag_depth_z", "Prior fifth-runner z", GOLD),
    ]
    for ax, col, title, c in panels:
        ax.scatter(d[col], d["state_place"], c=c, s=40, alpha=0.88, edgecolors="white", linewidths=0.5)
        band = pd.DataFrame({"x": d[col], "y": d["state_place"]})
        m = smf.ols("y ~ x", band).fit()
        xs = np.linspace(band["x"].min(), band["x"].max(), 60)
        pr = m.get_prediction(pd.DataFrame({"x": xs})).summary_frame()
        ax.plot(xs, pr["mean"], color=GRAY, lw=1.3)
        ax.fill_between(xs, pr["mean_ci_lower"], pr["mean_ci_upper"], color=GRAY, alpha=0.16)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(f"{title}\n(lower z = faster vs field)")
        ax.set_title(title.replace(" Prior-year ", "").replace("z", "").strip())
    axes[0].set_ylabel("Next-year team place (1 = best)")
    fig.suptitle("First- vs fifth-runner form versus next-year place", y=1.02, fontsize=12)
    fig.tight_layout()
    p = FIG / "figure3_star_depth.jpg"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["f3"] = p

    m = smf.ols(
        "state_place ~ log_enrollment + C(sector) + lag_depth_z",
        data=fit,
    ).fit(cov_type="cluster", cov_kwds={"groups": fit["school"], "use_correction": True})
    hold = hold.dropna(subset=["lag_depth_z", "log_enrollment", "sector"]).copy()
    hold["pred"] = m.predict(hold)
    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    ax.scatter(hold["state_place"], hold["pred"], c=TEAL, s=52, zorder=3, edgecolors="white", linewidths=0.5)
    lims = [0.3, max(hold["state_place"].max(), hold["pred"].max()) + 1.2]
    ax.plot(lims, lims, color=GRAY, ls="--", lw=1.2, label="Perfect match")
    for _, r in hold.iterrows():
        label = str(r["school"]).replace(" College", "").replace(" School", "")
        if len(label) > 14:
            label = label[:13] + "."
        ax.annotate(label, (r["state_place"], r["pred"]), fontsize=7.5, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("Observed 2025 team place (1 = best)")
    ax.set_ylabel("Predicted 2025 place (fifth-runner model)")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    p = FIG / "figure4_holdout.jpg"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    paths["f4"] = p
    return paths
