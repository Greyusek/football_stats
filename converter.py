"""Convert the working Excel database to CSV files for Streamlit Cloud.

Usage:
    python converter.py

The converter also restores Stats.player_name from Players by player_id.
This makes conversion independent of Excel formula cache values.
"""
from pathlib import Path
from typing import Dict, List, Union
import sys

import pandas as pd

DEFAULT_INPUTS = ("football_stats_new.xlsx", "football_stats.xlsx")
REQUIRED_SHEETS = {
    "Players": "players.csv",
    "Stats": "stats.csv",
    "Teams": "teams.csv",
    "Tournaments_n_Rules": "tournaments_n_rules.csv",
    "Achievements": "achievements.csv",
    "Hall_of_Fame": "hall_of_fame.csv",
}

DATE_COLUMNS = {
    "Stats": ["date", "check_tournament_start", "check_tournament_stop"],
    "Teams": ["date", "check_tournament_start", "check_tournament_stop"],
    "Tournaments_n_Rules": ["start", "end"],
    "Hall_of_Fame": ["date"],
}


def _pick_excel_file() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    for name in DEFAULT_INPUTS:
        path = Path(name)
        if path.exists():
            return path
    raise FileNotFoundError(
        "Не найден Excel-файл. Положите рядом football_stats_new.xlsx "
        "или запустите: python converter.py path/to/file.xlsx"
    )


def _normalize_dates(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    df = df.copy()
    for col in DATE_COLUMNS.get(sheet_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


def _normalize_tournament_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "tournament" in df.columns and "tournament_id" not in df.columns:
        df = df.rename(columns={"tournament": "tournament_id"})
    return df


def _clean_key(series: pd.Series) -> pd.Series:
    """Normalize identifiers for stable mapping between Excel sheets."""
    return series.astype("string").str.strip()


def _restore_player_names(stats: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Fill Stats.player_name using Players.player_id -> Players.player_name.

    Excel cells in Stats.player_name may contain formulas. openpyxl/pandas do not
    calculate formulas, and after workbook editing their cached results can be empty.
    Therefore player_id is treated as the source of truth.
    """
    stats = stats.copy()

    if "player_id" not in stats.columns:
        raise ValueError("На листе Stats отсутствует обязательный столбец player_id")
    if "player_id" not in players.columns or "player_name" not in players.columns:
        raise ValueError("На листе Players нужны столбцы player_id и player_name")

    player_map_df = players[["player_id", "player_name"]].copy()
    player_map_df["_player_key"] = _clean_key(player_map_df["player_id"])
    player_map_df["player_name"] = player_map_df["player_name"].astype("string").str.strip()
    player_map_df = player_map_df.dropna(subset=["_player_key"]).drop_duplicates("_player_key", keep="last")
    player_map: Dict[str, str] = player_map_df.set_index("_player_key")["player_name"].to_dict()

    stats["_player_key"] = _clean_key(stats["player_id"])
    restored = stats["_player_key"].map(player_map)

    if "player_name" not in stats.columns:
        stats["player_name"] = restored.astype("string")
    else:
        stats["player_name"] = stats["player_name"].astype("string")
        current = stats["player_name"].str.strip()
        missing = current.isna() | current.eq("") | current.str.lower().isin(["nan", "none", "неизвестно"])
        stats.loc[missing, "player_name"] = restored.loc[missing]

    # Last-resort fallback: show player_id instead of "Неизвестно".
    current = stats["player_name"].astype("string").str.strip()
    missing = current.isna() | current.eq("") | current.str.lower().isin(["nan", "none"])
    stats.loc[missing, "player_name"] = stats.loc[missing, "_player_key"]

    return stats.drop(columns=["_player_key"])


def convert_excel_to_csv(excel_file: Union[str, Path]) -> None:
    excel_file = Path(excel_file)
    xls = pd.ExcelFile(excel_file)

    missing = [sheet for sheet in REQUIRED_SHEETS if sheet not in xls.sheet_names]
    if missing:
        raise ValueError(f"В Excel не найдены обязательные листы: {', '.join(missing)}")

    sheets = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in REQUIRED_SHEETS}
    sheets["Stats"] = _restore_player_names(sheets["Stats"], sheets["Players"])

    written_files: List[str] = []
    for sheet_name, csv_name in REQUIRED_SHEETS.items():
        df = sheets[sheet_name]
        df = _normalize_dates(df, sheet_name)
        df = _normalize_tournament_id(df)
        df.to_csv(csv_name, index=False, encoding="utf-8")
        written_files.append(csv_name)

    print("Файлы успешно сохранены: " + ", ".join(written_files))


if __name__ == "__main__":
    convert_excel_to_csv(_pick_excel_file())
