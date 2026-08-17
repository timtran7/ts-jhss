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


_VARSITY_A = r"(?<!Junior\s)Varsity(?!\s*B\b)"


def _hytek_varsity_block(text: str, sex: str) -> str | None:
    """Return A varsity block only (exclude Varsity B / JV events)."""
    label = "Boys" if sex == "M" else "Girls"
    m = re.search(
        rf"Event\s+\d+\s+{label} 5k Run CC {_VARSITY_A}\b(.*?)(?=Event\s+\d+|\Z)",
        text,
        flags=re.I | re.S,
    )
    return m.group(1) if m else None


def _has_varsity_a(text: str, sex: str = "M") -> bool:
    if sex == "M":
        return bool(
            re.search(rf"Mens?\s+5,000\s+Meters\s+{_VARSITY_A}\b", text, flags=re.I)
            or re.search(rf"Boys\s+5k\s+Run\s+CC\s+{_VARSITY_A}\b", text, flags=re.I)
            or re.search(r"TEAM STANDINGS:\s*BOYS VARSITY\b", text, flags=re.I)
            or re.search(r"5K\s+Varsity\s+Boys\b", text, flags=re.I)
        )
    return bool(
        re.search(rf"Womens?\s+5,000\s+Meters\s+{_VARSITY_A}\b", text, flags=re.I)
        or re.search(rf"Girls\s+5k\s+Run\s+CC\s+{_VARSITY_A}\b", text, flags=re.I)
        or re.search(r"TEAM STANDINGS:\s*GIRLS VARSITY\b", text, flags=re.I)
        or re.search(r"5K\s+Varsity\s+Girls\b", text, flags=re.I)
    )


def _is_jv_only_archive(text: str) -> bool:
    """True when the file is a JV results page with no varsity-A content."""
    jv_markers = (
        "JV Boys",
        "JV Girls",
        "Junior Varsity",
        "5K JV Boys",
        "5K JV Girls",
        "Mens 5,000 Meters JV",
        "Womens 5,000 Meters JV",
    )
    has_jv = any(m.lower() in text.lower() for m in jv_markers)
    if not has_jv:
        return False
    return not (_has_varsity_a(text, "M") or _has_varsity_a(text, "F"))


def parse_ms_pre(text: str, season: int, alias_map: dict[str, str], sex: str = "M") -> tuple[list[dict], list[dict]]:
    inds, teams = [], []
    # Keep varsity A only (not Varsity B / Junior Varsity headings).
    if sex == "M":
        if not re.search(rf"Mens?\s+5,000\s+Meters\s+{_VARSITY_A}\b", text, flags=re.I):
            return inds, teams
        team_h = (
            rf"Mens?\s+5,000\s+Meters\s+{_VARSITY_A}\s+Team Scores"
            r"(.*?)"
            rf"Mens?\s+5,000\s+Meters\s+{_VARSITY_A}\s+Results"
        )
        res_h = (
            rf"Mens?\s+5,000\s+Meters\s+{_VARSITY_A}\s+Results"
            r"(.*?)(?=Mens?\s+5,000\s+Meters|\Z)"
        )
    else:
        if not re.search(rf"Womens?\s+5,000\s+Meters\s+{_VARSITY_A}\b", text, flags=re.I):
            return inds, teams
        team_h = (
            rf"Womens?\s+5,000\s+Meters\s+{_VARSITY_A}\s+Team Scores"
            r"(.*?)"
            rf"Womens?\s+5,000\s+Meters\s+{_VARSITY_A}\s+Results"
        )
        res_h = (
            rf"Womens?\s+5,000\s+Meters\s+{_VARSITY_A}\s+Results"
            r"(.*?)(?=Womens?\s+5,000\s+Meters|\Z)"
        )
    team_m = re.search(team_h, text, flags=re.I | re.S)
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
    res_m = re.search(res_h, text, flags=re.I | re.S)
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
                    "grade": int(m.group(3)),
                    "school": canonicalize(m.group(4), alias_map),
                    "time_sec": time_to_sec(m.group(5)),
                }
            )
    return inds, teams


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
                "grade": int(m.group(3)),
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
                "grade": int(m.group(3)),
                "school": school,
                "time_sec": time_to_sec(m.group(5)),
            }
        )
    return rows


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
                "grade": int(m.group(3)),
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
                "grade": int(m.group(3)),
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


def parse_pacers_team_standings(
    text: str, season: int, alias_map: dict[str, str], sex: str = "M"
) -> tuple[list[dict], list[dict]]:
    """Parse Pacers Running TEAM STANDINGS dumps (school blocks with places/times)."""
    label = "BOYS VARSITY" if sex == "M" else "GIRLS VARSITY"
    m = re.search(
        rf"TEAM STANDINGS:\s*{label}(.*?)(?=TEAM STANDINGS:|\Z)",
        text,
        flags=re.I | re.S,
    )
    if not m:
        return [], []
    block = m.group(1)
    teams: list[dict] = []
    inds: list[dict] = []
    header = re.compile(
        r"^\s*(\d+)\.\s+(\d+)\s+(.+?)\s+\(\s*" + TIME_TOKEN,
        re.M,
    )
    runner = re.compile(
        rf"^\s*\d+\s+(?:\(?\s*)?(\d+)\s*\)?\s+\d+\s+([A-Za-z].*?)\s+({TIME_TOKEN})\s*$",
        re.M,
    )
    parts = re.split(r"={5,}", block)
    # Alternating: header chunk, runner chunk, ...
    # First part may be blank/intro before first header.
    for chunk in parts:
        hm = header.search(chunk)
        if not hm:
            continue
        school = canonicalize(hm.group(3).strip(), alias_map)
        teams.append(
            {
                "season": season,
                "school": school,
                "state_place": int(hm.group(1)),
                "state_score": int(hm.group(2)),
            }
        )
    # Runner lines live after each ===== separator; walk with school from preceding header
    current_school = None
    for line in block.splitlines():
        hm = header.match(line)
        if hm:
            current_school = canonicalize(hm.group(3).strip(), alias_map)
            continue
        if current_school is None:
            continue
        rm = runner.match(line)
        if not rm:
            continue
        inds.append(
            {
                "season": season,
                "place": int(rm.group(1)),
                "athlete": rm.group(2).strip(),
                "school": current_school,
                "time_sec": time_to_sec(rm.group(3)),
            }
        )
    return inds, teams


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
    pa, pb = parse_pacers_team_standings(text, season, alias_map, sex=sex)
    inds.extend(pa)
    teams.extend(pb)
    if sex == "M":
        inds.extend(parse_html_or_md_table(text, season, alias_map))
    ind = pd.DataFrame(inds)
    team_df = pd.DataFrame(teams)
    if not ind.empty:
        ind = ind.drop_duplicates(subset=["season", "place", "school"])
        ind = ind[(ind["time_sec"] >= 14 * 60) & (ind["time_sec"] <= 45 * 60)]
        if "grade" in ind.columns:
            # Keep missing grades (Pacers dumps); drop middle-school ages when labeled.
            labeled = ind["grade"].notna()
            hs = ind["grade"].between(9, 12)
            ind = ind.loc[~labeled | hs].copy()
        ind["sex"] = sex
    if not team_df.empty:
        team_df = team_df.drop_duplicates(subset=["season", "school"], keep="first")
        team_df["sex"] = sex
    return ind, team_df


def parse_file(
    path: Path, season: int, alias_map: dict[str, str], sex: str = "M"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if _is_jv_only_archive(text):
        return pd.DataFrame(), pd.DataFrame()
    needles = (
        "Mens 5,000",
        "Boys 5k Run CC Varsity",
        "Womens 5,000",
        "Girls 5k Run CC Varsity",
        "TEAM STANDINGS:",
        "| Place |",
    )
    if "gtm.js" in text and not any(n in text for n in needles):
        return pd.DataFrame(), pd.DataFrame()
    return parse_result_text(text, season, alias_map, sex=sex)
