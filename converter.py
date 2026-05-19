"""Convert the working Excel database to CSV files for Streamlit Cloud.

Usage:
    python converter.py

By default the script reads football_stats_new.xlsx if it exists, otherwise
football_stats.xlsx. It writes CSV files used by main.py:
players.csv, stats.csv, teams.csv, tournaments_n_rules.csv.
"""
from pathlib import Path
from typing import List, Union
import sys
import pandas as pd

DEFAULT_INPUTS = ("football_stats_new.xlsx", "football_stats.xlsx")
REQUIRED_SHEETS = {
    "Players": "players.csv",
    "Stats": "stats.csv",
    "Teams": "teams.csv",
    "Tournaments_n_Rules": "tournaments_n_rules.csv",
}

DATE_COLUMNS = {
    "Stats": ["date", "check_tournament_start", "check_tournament_stop"],
    "Teams": ["date", "check_tournament_start", "check_tournament_stop"],
    "Tournaments_n_Rules": ["start", "end"],
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
    for col in DATE_COLUMNS.get(sheet_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


def _normalize_tournament_id(df: pd.DataFrame) -> pd.DataFrame:
    # In Stats/Teams the current workbook uses the column name `tournament`
    # as a foreign key to Tournaments_n_Rules.tournament_id.
    if "tournament" in df.columns and "tournament_id" not in df.columns:
        df = df.rename(columns={"tournament": "tournament_id"})
    return df


def convert_excel_to_csv(excel_file: Union[str, Path]) -> None:
    excel_file = Path(excel_file)
    xls = pd.ExcelFile(excel_file)

    missing = [sheet for sheet in REQUIRED_SHEETS if sheet not in xls.sheet_names]
    if missing:
        raise ValueError(f"В Excel не найдены обязательные листы: {', '.join(missing)}")

    written_files: List[str] = []
    for sheet_name, csv_name in REQUIRED_SHEETS.items():
        df = pd.read_excel(xls, sheet_name=sheet_name)
        df = _normalize_dates(df, sheet_name)
        df = _normalize_tournament_id(df)
        df.to_csv(csv_name, index=False, encoding="utf-8")
        written_files.append(csv_name)

    print("Файлы успешно сохранены: " + ", ".join(written_files))


if __name__ == "__main__":
    convert_excel_to_csv(_pick_excel_file())
