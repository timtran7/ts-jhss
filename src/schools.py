"""School name normalization."""

from __future__ import annotations

import pandas as pd


def load_school_lookup(path: str = "data/schools.csv") -> tuple[pd.DataFrame, dict[str, str]]:
    schools = pd.read_csv(path)
    alias_map: dict[str, str] = {}
    for _, row in schools.iterrows():
        alias_map[_norm(row["canonical"])] = row["canonical"]
        for alias in str(row["aliases"]).split(";"):
            alias_map[_norm(alias)] = row["canonical"]
    return schools, alias_map


def _norm(name: str) -> str:
    s = name.lower().strip()
    for ch in ".,'":
        s = s.replace(ch, "")
    s = " ".join(s.split())
    for suffix in (
        " high school",
        " high s",
        " school",
        " pcs",
        " public c",
        " college high",
        " college",
    ):
        if s.endswith(suffix) and s != suffix.strip():
            s = s[: -len(suffix)].strip()
    replacements = {
        "woodrow wils": "jackson-reed",
        "woodrow wilson": "jackson-reed",
        "wilson": "jackson-reed",
        "st johns": "st johns college",
        "st johns c": "st johns college",
        "gonzaga coll": "gonzaga",
        "sidwell frie": "sidwell friends",
        "georgetown d": "georgetown day",
        "georgetown v": "georgetown visitation",
        "washington l": "washington latin",
        "washington i": "washington international",
        "eastern": "eastern",
        "e.l. haynes": "el haynes",
        "el haynes": "el haynes",
        "e l haynes": "el haynes",
        "dc internati": "dc international",
        "mckinley tec": "mckinley technology",
        "mckinley tech": "mckinley technology",
        "phelps caree": "phelps career",
        "kipp dc college prep": "kipp dc college prep",
        "kipp dc": "kipp dc college prep",
        "basis dc": "basis dc",
        "school without walls (dc)": "school without walls",
        "school without walls high": "school without walls",
        "st albans": "st albans",
        "georgetown visitation pre": "georgetown visitation",
        "bell high": "bell multicultural",
    }
    return replacements.get(s, s)


def canonicalize(name: str, alias_map: dict[str, str]) -> str:
    key = _norm(name)
    if key in alias_map:
        return alias_map[key]
    for alias, canon in alias_map.items():
        if not alias or len(alias) < 10:
            continue
        if alias == key or (alias in key and len(alias) / max(len(key), 1) > 0.6):
            return canon
    return name.strip()
