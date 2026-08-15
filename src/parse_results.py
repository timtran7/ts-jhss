"""Parse MileSplit / HY-TEK championship result text."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.schools import canonicalize, load_school_lookup

TIME_TOKEN = r"(?:(?:\d+:)?\d+:\d{2}(?:\.\d+)?)"


def time_to_sec(text: str) -> float:
    text = text.strip().lstrip("0")
    if text.startswith(":"):
        text = "0" + text
    parts = text.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(text)


def _extract_pre(text: str) -> str:
    blocks = re.findall(r"<pre>(.*?)</pre>", text, flags=re.I | re.S)
    if blocks:
        return "\n".join(blocks)
    return text


def _hytek_varsity_block(text: str, sex: str) -> str | None:
    label = "Boys" if sex == "M" else "Girls"
    m = re.search(
        rf"Event\s+\d+\s+{label} 5k Run CC Varsity(.*?)(?=Event\s+\d+|\Z)",
        text,
        flags=re.I | re.S,
    )
    return m.group(1) if m else None


def parse_hytek_individuals(block: str, season: int, alias_map: dict[str, str]) -> list[dict]:
    rows = []
    # place, last, first, year, school, time
    pat = re.compile(
        rf"^\s*(\d+)\s+([A-Za-z].*?)\s+(\d{{1,2}})\s+(.+?)\s+({TIME_TOKEN})\s+",
        re.M,
    )
    for m in pat.finditer(block):
        school = canonicalize(m.group(4).strip(), alias_map)
        rows.append(
            {
                "season": season,
                "place": int(m.group(1)),
                "athlete": m.group(2).strip(" ,"),
                "school": school,
                "time_sec": time_to_sec(m.group(5)),
            }
        )
    if rows:
        return rows
    # MileSplit raw dumps often collapse HY-TEK onto one line
    inline = re.compile(
        rf"(\d+)\s+([A-Za-z][A-Za-z'. -]+,\s+[A-Za-z][A-Za-z'. -]+)\s+(\d{{1,2}})\s+(.+?)\s+({TIME_TOKEN})(?:\s+\d+|\s+--|\s+DNF)?"
    )
    seen = set()
    for m in inline.finditer(block):
        place = int(m.group(1))
        if place in seen or place > 250:
            continue
        seen.add(place)
        school = canonicalize(m.group(4).strip(), alias_map)
        rows.append(
            {
                "season": season,
                "place": place,
                "athlete": m.group(2).strip(" ,"),
                "school": school,
                "time_sec": time_to_sec(m.group(5)),
            }
        )
    return rows


def parse_ms_pre(text: str, season: int, alias_map: dict[str, str], sex: str = "M") -> tuple[list[dict], list[dict]]:
    inds, teams = [], []
    if sex == "M":
        if "Mens 5,000 Meters Varsity" not in text and "Men's 5,000 Meters Varsity" not in text:
            return inds, teams
        team_h = r"Mens 5,000 Meters Varsity Team Scores(.*?)Mens 5,000 Meters Varsity Results"
        res_h = r"Mens 5,000 Meters Varsity Results(.*)"
    else:
        if "Womens 5,000 Meters Varsity" not in text and "Women's 5,000 Meters Varsity" not in text:
            return inds, teams
        team_h = r"Womens 5,000 Meters Varsity Team Scores(.*?)Womens 5,000 Meters Varsity Results"
        res_h = r"Womens 5,000 Meters Varsity Results(.*)"
    team_m = re.search(team_h, text, flags=re.S)
    if team_m:
        for m in re.finditer(r"^\s*(\d+)\s+(.+?)\s+(\d+)\s*$", team_m.group(1), re.M):
            teams.append(
                {
                    "season": season,
                    "school": canonicalize(m.group(2), alias_map),
                    "state_place": int(m.group(1)),
                    "state_score": int(m.group(3)),
                }
            )
    res_m = re.search(res_h, text, flags=re.S)
    if res_m:
        for m in re.finditer(
            rf"^\s*(\d+)\s+(.+?)\s+(\d{{1,2}})\s+(.+?)\s+({TIME_TOKEN})\s*$",
            res_m.group(1),
            re.M,
        ):
            inds.append(
                {
                    "season": season,
                    "place": int(m.group(1)),
                    "athlete": m.group(2).strip(),
                    "school": canonicalize(m.group(4), alias_map),
                    "time_sec": time_to_sec(m.group(5)),
                }
            )
    return inds, teams


def parse_html_or_md_table(text: str, season: int, alias_map: dict[str, str]) -> list[dict]:
    rows = []
    for m in re.finditer(
        rf"<tr><td>(\d+)</td><td>([^<]+)</td><td>(\d+)</td><td>([^<]+)</td><td>({TIME_TOKEN})",
        text,
    ):
        rows.append(
            {
                "season": season,
                "place": int(m.group(1)),
                "athlete": m.group(2).strip(),
                "school": canonicalize(m.group(4), alias_map),
                "time_sec": time_to_sec(m.group(5)),
            }
        )
    for m in re.finditer(
        rf"^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*(\d+)\s*\|\s*([^|]+)\|\s*({TIME_TOKEN})",
        text,
        re.M,
    ):
        rows.append(
            {
                "season": season,
                "place": int(m.group(1)),
                "athlete": m.group(2).strip(),
                "school": canonicalize(m.group(4), alias_map),
                "time_sec": time_to_sec(m.group(5)),
            }
        )
    return rows


def parse_hytek_teams(block: str, season: int, alias_map: dict[str, str], sex: str = "M") -> list[dict]:
    rows = []
    blob = block
    gender = "Men" if sex == "M" else "Women"
    m = re.search(rf"Team Scores.*?Results - {gender}(.*?)(?=Event\s+\d+|\Z)", block, flags=re.I | re.S)
    if m:
        blob = m.group(1)
    for tm in re.finditer(
        r"(?:^|\s)(\d{1,2})\s+([A-Za-z][A-Za-z0-9'. :-]{6,40}?)\s+(\d{1,3})\s+(\d{1,3})\s+\d+",
        blob,
    ):
        school = canonicalize(tm.group(2).strip(), alias_map)
        rows.append(
            {
                "season": season,
                "school": school,
                "state_place": int(tm.group(1)),
                "state_score": int(tm.group(3)),
            }
        )
    return rows


def parse_result_text(
    text: str, season: int, alias_map: dict[str, str], sex: str = "M"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    text = _extract_pre(text.replace("\r\n", "\n").replace("\r", "\n"))
    inds: list[dict] = []
    teams: list[dict] = []
    block = _hytek_varsity_block(text, sex)
    if block:
        inds.extend(parse_hytek_individuals(block, season, alias_map))
        teams.extend(parse_hytek_teams(block, season, alias_map, sex=sex))
    a, b = parse_ms_pre(text, season, alias_map, sex=sex)
    inds.extend(a)
    teams.extend(b)
    if sex == "M":
        inds.extend(parse_html_or_md_table(text, season, alias_map))
    ind = pd.DataFrame(inds)
    team_df = pd.DataFrame(teams)
    if not ind.empty:
        ind = ind.drop_duplicates(subset=["season", "place", "school"])
        ind = ind[(ind["time_sec"] >= 14 * 60) & (ind["time_sec"] <= 45 * 60)]
        ind["sex"] = sex
    if not team_df.empty:
        team_df["sex"] = sex
    return ind, team_df


def parse_file(
    path: Path, season: int, alias_map: dict[str, str], sex: str = "M"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    needles = (
        "Mens 5,000",
        "Boys 5k Run CC Varsity",
        "Womens 5,000",
        "Girls 5k Run CC Varsity",
        "| Place |",
    )
    if "gtm.js" in text and not any(n in text for n in needles):
        return pd.DataFrame(), pd.DataFrame()
    return parse_result_text(text, season, alias_map, sex=sex)
