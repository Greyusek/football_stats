from typing import Dict, List, Tuple
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Футбол в Митино", layout="wide")

st.markdown(
    """
    <style>
        /* Общая компоновка: компактно и влево */
        .block-container {
            max-width: 1120px;
            padding-top: 1.0rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 1rem;
            margin-left: 0 !important;
            margin-right: auto !important;
        }

        h1, h2, h3 {
            text-align: left !important;
            margin-bottom: 0.65rem !important;
        }

        .element-container {
            margin-bottom: 0.35rem !important;
        }

        div[data-testid="stDataFrame"] {
            margin-left: 0 !important;
            margin-right: auto !important;
        }

        .classic-summary {
            max-width: 560px;
            margin-left: 0;
            margin-right: auto;
            padding-top: 4px;
        }

        .classic-summary h1 {
            text-align: left !important;
            font-size: 2.45rem;
            line-height: 1.2;
            margin-bottom: 1.5rem;
        }

        .classic-summary .line {
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.45;
            margin: 1.15rem 0;
        }

        .classic-summary .footer-left {
            margin-top: 1.6rem;
            font-size: 0.95rem;
        }

        .rules-box {
            max-width: 430px;
            margin: 18px auto 0 0;
        }

        .footer {
            text-align: left;
            color: #777;
            margin-top: 24px;
        }

        section[data-testid="stSidebar"] {
            width: 270px !important;
        }

        .js-plotly-plot {
            margin-left: 0 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

STAT_COLUMNS = {
    "goals": "goals_on_date",
    "assists": "assists_on_date",
    "wins": "wins_on_date",
    "draws": "draws_on_date",
    "saves": "saves_on_date",
    "foul": "foul_on_date",
}

COEFFICIENT_COLUMNS = {
    "goals": "goals_coefficient",
    "assists": "assists_coefficient",
    "wins": "wins_coefficient",
    "draws": "draws_coefficient",
    "saves": "saves_coefficient",
    "foul": "foul_coefficient",
}

DISPLAY_COLUMNS = {
    "date": "Число",
    "team_number": "№ команды",
    "player_name": "Игрок",
    "goals_on_date": "Голы",
    "assists_on_date": "Пасы",
    "wins_on_date": "Победы",
    "draws_on_date": "Ничьи",
    "saves_on_date": "На ноль",
    "foul_on_date": "Фолы",
    "points": "Очки",
}

TOP_TABLES = [
    ("Общий рейтинг", "points", "Очки"),
    ("Топ бомбардиров", "goals", "Голы"),
    ("Топ раздающих", "assists", "Пасы"),
    ("Топ голкиперов", "saves", "На ноль"),
    ("Количество побед", "wins", "Побед"),
    ("Количество ничьих", "draws", "Ничьих"),
    ("Фолы", "foul", "Фолы"),
]


@st.cache_data
def load_data():
    players = pd.read_csv("players.csv")
    stats = pd.read_csv("stats.csv")
    teams = pd.read_csv("teams.csv")
    rules = pd.read_csv("tournaments_n_rules.csv")

    for df in (stats, teams):
        if "tournament" in df.columns and "tournament_id" not in df.columns:
            df.rename(columns={"tournament": "tournament_id"}, inplace=True)

    for df in (stats, teams):
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "tournament_id" in df.columns:
            df["tournament_id"] = pd.to_numeric(df["tournament_id"], errors="coerce").astype("Int64")

    rules["tournament_id"] = pd.to_numeric(rules["tournament_id"], errors="coerce").astype("Int64")
    rules["start"] = pd.to_datetime(rules["start"], errors="coerce")
    rules["end"] = pd.to_datetime(rules["end"], errors="coerce")

    if "player_name" in players.columns:
        players["player_name"] = players["player_name"].fillna("Неизвестно").astype(str)
    if "player_name" in stats.columns:
        stats["player_name"] = stats["player_name"].fillna("Неизвестно").astype(str)

    for column in STAT_COLUMNS.values():
        if column not in stats.columns:
            stats[column] = 0
        stats[column] = pd.to_numeric(stats[column], errors="coerce").fillna(0)

    for column in ("wins_on_date", "draws_on_date"):
        if column not in teams.columns:
            teams[column] = 0
        teams[column] = pd.to_numeric(teams[column], errors="coerce").fillna(0)

    for column in COEFFICIENT_COLUMNS.values():
        if column not in rules.columns:
            rules[column] = 0
        rules[column] = pd.to_numeric(rules[column], errors="coerce").fillna(0)

    return players, stats, teams, rules


def centered_dataframe(df: pd.DataFrame, height: int = None, width: int = 560, use_container_width: bool = False):
    """Историческое имя функции оставлено, но теперь таблицы выводятся слева."""
    if use_container_width:
        st.dataframe(df, hide_index=True, height=height, use_container_width=True)
    else:
        st.dataframe(df, hide_index=True, height=height, width=width)


def full_dataframe(df: pd.DataFrame, height: int = None):
    st.dataframe(df, hide_index=True, height=height, use_container_width=True)


def ceil_number(value) -> int:
    """Округляет расчетное количество игр вверх до целого для человекочитаемого вывода."""
    try:
        if pd.isna(value):
            return 0
        return int(math.ceil(float(value)))
    except Exception:
        return 0


def get_tournament_rules(rules: pd.DataFrame, tournament_id: int) -> pd.Series:
    row = rules[rules["tournament_id"] == tournament_id]
    if row.empty:
        st.error("Не найдены правила для выбранного турнира")
        st.stop()
    return row.iloc[0]


def filter_by_tournament(stats: pd.DataFrame, teams: pd.DataFrame, rule: pd.Series):
    tournament_id = int(rule["tournament_id"])
    start = rule["start"]
    end = rule["end"]

    stats_filtered = stats[
        (stats["tournament_id"] == tournament_id)
        & (stats["date"] >= start)
        & (stats["date"] <= end)
    ].copy()
    teams_filtered = teams[
        (teams["tournament_id"] == tournament_id)
        & (teams["date"] >= start)
        & (teams["date"] <= end)
    ].copy()
    return stats_filtered, teams_filtered


def add_points(df: pd.DataFrame, rule: pd.Series) -> pd.DataFrame:
    df = df.copy()
    df["points"] = 0
    for stat_name, value_column in STAT_COLUMNS.items():
        if value_column in df.columns:
            df["points"] += df[value_column] * rule[COEFFICIENT_COLUMNS[stat_name]]
    return df


def aggregate_players(stats_filtered: pd.DataFrame, rule: pd.Series) -> pd.DataFrame:
    if stats_filtered.empty:
        return pd.DataFrame(columns=["player_name", "goals", "assists", "wins", "draws", "saves", "foul", "points"])

    group_columns = ["player_name"]
    if "player_id" in stats_filtered.columns:
        group_columns.insert(0, "player_id")

    agg_map = {column: "sum" for column in STAT_COLUMNS.values() if column in stats_filtered.columns}
    result = stats_filtered.groupby(group_columns, as_index=False).agg(agg_map)

    result = result.rename(columns={value: key for key, value in STAT_COLUMNS.items()})
    result["points"] = 0
    for stat_name in STAT_COLUMNS:
        if stat_name in result.columns:
            result["points"] += result[stat_name] * rule[COEFFICIENT_COLUMNS[stat_name]]
    return result.sort_values("points", ascending=False)


def season_summary(stats_filtered: pd.DataFrame, teams_filtered: pd.DataFrame) -> Dict[str, int]:
    total_wins = int(teams_filtered["wins_on_date"].sum()) if not teams_filtered.empty else 0
    total_draws = int(teams_filtered["draws_on_date"].sum() / 2) if not teams_filtered.empty else 0
    return {
        "games": total_wins + total_draws,
        "draws": total_draws,
        "goals": int(stats_filtered["goals_on_date"].sum()) if not stats_filtered.empty else 0,
        "assists": int(stats_filtered["assists_on_date"].sum()) if not stats_filtered.empty else 0,
        "saves": int(stats_filtered["saves_on_date"].sum()) if not stats_filtered.empty else 0,
        "fouls": int(stats_filtered["foul_on_date"].sum()) if not stats_filtered.empty else 0,
    }


def tournament_title(rule: pd.Series) -> str:
    return '{} ({})'.format(rule["season"], str(rule["tournament_name"]).upper())


def season_label(row) -> str:
    return str(row.season)




def add_points_with_rules(stats_df: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    """Начисляет очки по правилам каждого турнира. Используется для глобальной аналитики."""
    if stats_df.empty:
        result = stats_df.copy()
        result["points"] = 0
        return result

    coeff_columns = ["tournament_id"] + list(COEFFICIENT_COLUMNS.values())
    rules_short = rules[coeff_columns].drop_duplicates("tournament_id")
    result = stats_df.copy().merge(rules_short, on="tournament_id", how="left")
    result["points"] = 0
    for stat_name, value_column in STAT_COLUMNS.items():
        coeff_column = COEFFICIENT_COLUMNS[stat_name]
        if value_column in result.columns and coeff_column in result.columns:
            result["points"] += result[value_column].fillna(0) * result[coeff_column].fillna(0)
    return result


def _fallback_team_games(day_teams: pd.DataFrame) -> Dict[int, float]:
    """Резервная оценка, если точную последовательность игр восстановить нельзя."""
    rows = []
    for _, row in day_teams.iterrows():
        team = int(row["team_number"])
        wins = float(row.get("wins_on_date", 0) or 0)
        draws = float(row.get("draws_on_date", 0) or 0)
        rows.append((team, wins, draws))

    total_wins = sum(x[1] for x in rows)
    total_draw_marks = sum(x[2] for x in rows)
    total_games = total_wins + total_draw_marks / 2.0
    total_team_games = total_games * 2.0
    known_team_games = total_wins + total_draw_marks
    losses_to_distribute = max(total_team_games - known_team_games, 0)

    # Чем меньше у команды побед/ничьих, тем вероятнее у нее больше поражений.
    strengths = {team: wins + draws for team, wins, draws in rows}
    max_strength = max(strengths.values()) if strengths else 0
    weights = {team: max_strength - value + 1 for team, value in strengths.items()}
    weight_sum = sum(weights.values()) or 1

    result = {}
    for team, wins, draws in rows:
        estimated_losses = losses_to_distribute * weights[team] / weight_sum
        result[team] = wins + draws + estimated_losses
    return result


def estimate_team_games_for_day(day_teams: pd.DataFrame) -> Dict[int, float]:
    """
    Оценивает количество реально сыгранных игр каждой командой за игровой день.

    В Teams есть только победы и ничьи. Поражения явно не хранятся, поэтому точную
    историю игр не всегда можно восстановить. Для небольших игровых дней функция
    пробует восстановить последовательность по правилам:
    - победитель остается, проигравший садится;
    - при ничьей для 3 команд садится команда с большей текущей серией игр;
    - при ничьей для 4+ команд садятся обе команды.

    Если однозначно восстановить не получилось, используется резервная оценка.
    """
    if day_teams.empty or "team_number" not in day_teams.columns:
        return {}

    compact = day_teams[["team_number", "wins_on_date", "draws_on_date"]].copy()
    compact["team_number"] = pd.to_numeric(compact["team_number"], errors="coerce")
    compact = compact.dropna(subset=["team_number"])
    if compact.empty:
        return {}

    grouped = compact.groupby("team_number", as_index=False).agg({
        "wins_on_date": "sum",
        "draws_on_date": "sum",
    })
    teams_list = [int(x) for x in sorted(grouped["team_number"].unique())]
    if len(teams_list) < 2:
        return {teams_list[0]: 0} if teams_list else {}

    wins_left = {int(r.team_number): int(r.wins_on_date) for r in grouped.itertuples()}
    draws_left = {int(r.team_number): int(r.draws_on_date) for r in grouped.itertuples()}
    draw_marks = sum(draws_left.values())
    if draw_marks % 2 != 0:
        return _fallback_team_games(grouped)

    total_games = sum(wins_left.values()) + draw_marks // 2
    if total_games <= 0:
        return {team: 0 for team in teams_list}
    if len(teams_list) > 6 or total_games > 18:
        return _fallback_team_games(grouped)

    initial_active = (teams_list[0], teams_list[1])
    initial_queue = tuple(teams_list[2:])
    initial_streak = {team: 0 for team in teams_list}
    initial_counts = {team: 0 for team in teams_list}
    solutions = []

    def rotate_after_win(winner, loser, queue):
        queue = list(queue)
        if queue:
            new_team = queue.pop(0)
            queue.append(loser)
            return (winner, new_team), tuple(queue)
        return (winner, loser), tuple(queue)

    def rotate_after_draw(a, b, queue, streak):
        queue = list(queue)
        if len(teams_list) <= 2:
            return [(a, b, tuple(queue))]
        if len(teams_list) == 3:
            sit_candidates = []
            if streak[a] > streak[b]:
                sit_candidates = [a]
            elif streak[b] > streak[a]:
                sit_candidates = [b]
            else:
                sit_candidates = [a, b]

            variants = []
            for sit in sit_candidates:
                stay = b if sit == a else a
                q = list(queue)
                new_team = q.pop(0) if q else sit
                q.append(sit)
                variants.append((stay, new_team, tuple(q)))
            return variants

        # 4+ команд: по ничьей садятся обе активные команды.
        q = list(queue)
        q.extend([a, b])
        if len(q) >= 2:
            return [(q.pop(0), q.pop(0), tuple(q))]
        return [(a, b, tuple(q))]

    def can_still_finish(step, wins, draws):
        remaining_games = total_games - step
        return sum(wins.values()) + sum(draws.values()) // 2 == remaining_games

    def rec(step, active, queue, wins, draws, streak, counts):
        if len(solutions) >= 1:
            return
        if step == total_games:
            if all(v == 0 for v in wins.values()) and all(v == 0 for v in draws.values()):
                solutions.append(counts.copy())
            return
        if not can_still_finish(step, wins, draws):
            return

        a, b = active
        outcomes = []
        if wins.get(a, 0) > 0:
            outcomes.append(("win", a, b))
        if wins.get(b, 0) > 0:
            outcomes.append(("win", b, a))
        if draws.get(a, 0) > 0 and draws.get(b, 0) > 0:
            outcomes.append(("draw", a, b))

        for kind, x, y in outcomes:
            new_wins = wins.copy()
            new_draws = draws.copy()
            new_streak = streak.copy()
            new_counts = counts.copy()
            new_counts[a] += 1
            new_counts[b] += 1
            new_streak[a] += 1
            new_streak[b] += 1

            if kind == "win":
                winner, loser = x, y
                new_wins[winner] -= 1
                new_streak[loser] = 0
                new_active, new_queue = rotate_after_win(winner, loser, queue)
                # Вновь вышедшая команда начинает серию с 0.
                for team in new_active:
                    new_streak.setdefault(team, 0)
                rec(step + 1, new_active, new_queue, new_wins, new_draws, new_streak, new_counts)
            else:
                new_draws[a] -= 1
                new_draws[b] -= 1
                for na, nb, nq in rotate_after_draw(a, b, queue, new_streak):
                    streak_variant = new_streak.copy()
                    inactive = set(teams_list) - {na, nb}
                    for team in inactive:
                        if team in (a, b):
                            streak_variant[team] = 0
                    rec(step + 1, (na, nb), nq, new_wins, new_draws, streak_variant, new_counts)

    rec(0, initial_active, initial_queue, wins_left, draws_left, initial_streak, initial_counts)
    if solutions:
        return {team: float(value) for team, value in solutions[0].items()}
    return _fallback_team_games(grouped)


def build_team_games_map(teams_scope: pd.DataFrame) -> Dict[Tuple[int, pd.Timestamp, int], float]:
    """Карта: (tournament_id, date, team_number) -> расчетное количество игр команды в этот день."""
    if teams_scope.empty or "team_number" not in teams_scope.columns:
        return {}

    data = teams_scope.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date", "tournament_id", "team_number"])
    if data.empty:
        return {}

    result = {}
    for (tournament_id, date), day_df in data.groupby(["tournament_id", "date"]):
        counts = estimate_team_games_for_day(day_df)
        for team_number, games in counts.items():
            result[(int(tournament_id), pd.Timestamp(date), int(team_number))] = float(games)
    return result


def attach_estimated_games(stats_scope: pd.DataFrame, teams_scope: pd.DataFrame) -> pd.DataFrame:
    """Добавляет к строкам stats расчетное количество игр команды за игровой день."""
    data = stats_scope.copy()
    if data.empty:
        data["estimated_games"] = 0.0
        return data

    game_map = build_team_games_map(teams_scope)
    if "team_number" not in data.columns:
        data["estimated_games"] = 1.0
        return data

    def lookup(row):
        try:
            key = (int(row["tournament_id"]), pd.Timestamp(row["date"]), int(row["team_number"]))
            return game_map.get(key, 1.0)
        except Exception:
            return 1.0

    data["estimated_games"] = data.apply(lookup, axis=1)
    return data


def calculate_efficiency_index(
    stats_scope: pd.DataFrame,
    teams_scope: pd.DataFrame,
    rules: pd.DataFrame = None,
    rule: pd.Series = None,
) -> pd.DataFrame:
    """Индекс эффективности 0..1: 70% результативность за игру + 30% объем сыгранных игр."""
    if stats_scope.empty:
        return pd.DataFrame()

    if rule is not None:
        data = add_points(stats_scope, rule)
    else:
        data = add_points_with_rules(stats_scope, rules)

    data = attach_estimated_games(data, teams_scope)

    grouped = data.groupby("player_name", as_index=False).agg({
        "points": "sum",
        "goals_on_date": "sum",
        "assists_on_date": "sum",
        "wins_on_date": "sum",
        "draws_on_date": "sum",
        "saves_on_date": "sum",
        "foul_on_date": "sum",
        "estimated_games": "sum",
    })

    grouped["estimated_games"] = grouped["estimated_games"].replace(0, 1)
    grouped["points_per_game"] = grouped["points"] / grouped["estimated_games"]

    max_ppg = max(float(grouped["points_per_game"].max()), 1.0)
    max_games = max(float(grouped["estimated_games"].max()), 1.0)
    grouped["result_norm"] = (grouped["points_per_game"] / max_ppg).clip(lower=0, upper=1)
    grouped["regularity_norm"] = (grouped["estimated_games"] / max_games).clip(lower=0, upper=1)
    grouped["efficiency_index"] = (0.7 * grouped["result_norm"] + 0.3 * grouped["regularity_norm"]).clip(0, 1)

    grouped = grouped.rename(columns={
        "player_name": "Игрок",
        "estimated_games": "Игры",
        "points": "Очки",
        "points_per_game": "Очки/игру",
        "goals_on_date": "Голы",
        "assists_on_date": "Пасы",
        "wins_on_date": "Победы",
        "draws_on_date": "Ничьи",
        "saves_on_date": "На ноль",
        "foul_on_date": "Фолы",
        "efficiency_index": "Индекс",
    })

    result_columns = ["Игрок", "Индекс", "Игры", "Очки", "Очки/игру", "Голы", "Пасы", "Победы", "Ничьи", "На ноль", "Фолы"]
    result = grouped[result_columns].sort_values(["Индекс", "Очки"], ascending=False)
    result["Индекс"] = result["Индекс"].round(3)
    result["Очки/игру"] = result["Очки/игру"].round(3)
    result["Игры"] = result["Игры"].apply(ceil_number).astype(int)
    result["Очки"] = result["Очки"].round(2)
    return result


def calculate_partners(
    stats_scope: pd.DataFrame,
    teams_scope: pd.DataFrame,
    player_name: str,
    rules: pd.DataFrame = None,
    rule: pd.Series = None,
) -> pd.DataFrame:
    """Партнеры игрока: кто чаще и результативнее играл с ним в одной команде."""
    if stats_scope.empty or "team_number" not in stats_scope.columns:
        return pd.DataFrame()

    if rule is not None:
        data = add_points(stats_scope, rule)
    else:
        data = add_points_with_rules(stats_scope, rules)

    data = attach_estimated_games(data, teams_scope)

    key_cols = [c for c in ["tournament_id", "date", "team_number"] if c in data.columns]
    selected = data[data["player_name"] == player_name].copy()
    if selected.empty:
        return pd.DataFrame()

    selected_cols = key_cols + ["player_name", "points", "wins_on_date", "draws_on_date", "goals_on_date", "assists_on_date", "estimated_games"]
    partner_cols = key_cols + ["player_name", "points", "goals_on_date", "assists_on_date"]
    selected = selected[selected_cols].rename(columns={
        "player_name": "selected_player",
        "points": "selected_points",
        "wins_on_date": "selected_wins",
        "draws_on_date": "selected_draws",
        "goals_on_date": "selected_goals",
        "assists_on_date": "selected_assists",
        "estimated_games": "games_together",
    })
    partners = data[partner_cols].rename(columns={
        "player_name": "partner",
        "points": "partner_points",
        "goals_on_date": "partner_goals",
        "assists_on_date": "partner_assists",
    })

    pairs = selected.merge(partners, on=key_cols, how="inner")
    pairs = pairs[pairs["partner"] != player_name].copy()
    if pairs.empty:
        return pd.DataFrame()

    pairs["pair_points"] = pairs["selected_points"] + pairs["partner_points"]
    pairs["pair_goals_assists"] = (
        pairs["selected_goals"] + pairs["selected_assists"] + pairs["partner_goals"] + pairs["partner_assists"]
    )

    agg = pairs.groupby("partner", as_index=False).agg({
        "pair_points": "sum",
        "pair_goals_assists": "sum",
        "selected_wins": "sum",
        "selected_draws": "sum",
        "games_together": "sum",
    })
    agg["pair_points_per_game"] = agg["pair_points"] / agg["games_together"].replace(0, 1)

    max_games = max(float(agg["games_together"].max()), 1.0)
    max_ppg = max(float(agg["pair_points_per_game"].max()), 1.0)
    agg["link_index"] = (
        0.5 * (agg["games_together"] / max_games).clip(0, 1)
        + 0.5 * (agg["pair_points_per_game"] / max_ppg).clip(lower=0, upper=1)
    ).clip(0, 1)

    agg = agg.rename(columns={
        "partner": "Партнер",
        "games_together": "Игр вместе",
        "selected_wins": "Побед вместе",
        "selected_draws": "Ничьих вместе",
        "pair_goals_assists": "Голы+пасы пары",
        "pair_points": "Очки пары",
        "pair_points_per_game": "Очки пары/игру",
        "link_index": "Индекс связки",
    })
    result = agg[["Партнер", "Индекс связки", "Игр вместе", "Побед вместе", "Ничьих вместе", "Голы+пасы пары", "Очки пары", "Очки пары/игру"]]
    result = result.sort_values(["Индекс связки", "Игр вместе"], ascending=False)
    result["Индекс связки"] = result["Индекс связки"].round(3)
    result["Очки пары/игру"] = result["Очки пары/игру"].round(3)
    result["Игр вместе"] = result["Игр вместе"].apply(ceil_number).astype(int)
    result["Очки пары"] = result["Очки пары"].round(2)
    return result


def analytics_season_options(rules: pd.DataFrame) -> Tuple[List[str], Dict[str, int]]:
    options = ["За все время"]
    label_to_id = {}
    sorted_rules = rules.sort_values(["start", "tournament_name"], ascending=[False, True])
    for row in sorted_rules.itertuples():
        label = "{} — {}".format(row.season, row.tournament_name)
        if label in label_to_id:
            label = "{} ({})".format(label, int(row.tournament_id))
        options.append(label)
        label_to_id[label] = int(row.tournament_id)
    return options, label_to_id


def show_analytics(stats: pd.DataFrame, teams: pd.DataFrame, rules: pd.DataFrame):
    st.title("Аналитика")

    options, label_to_id = analytics_season_options(rules)
    selected_period = st.selectbox("Выберите сезон:", options)

    if selected_period == "За все время":
        scope_stats = stats.copy()
        scope_teams = teams.copy()
        efficiency = calculate_efficiency_index(scope_stats, scope_teams, rules=rules)
        partners_rule = None
        partners_rules = rules
    else:
        rule = get_tournament_rules(rules, label_to_id[selected_period])
        scope_stats, scope_teams = filter_by_tournament(stats, teams, rule)
        efficiency = calculate_efficiency_index(scope_stats, scope_teams, rule=rule)
        partners_rule = rule
        partners_rules = None

    st.markdown(
        """
        **Формула индекса эффективности:**  
        `Индекс = 0.7 × результативность + 0.3 × регулярность`  
        `результативность = очки игрока за игру / лучший показатель очков за игру`  
        `регулярность = расчетное количество игр игрока / максимум игр среди игроков`

        Важно: расчет выполняется отдельно по каждому игровому дню и команде, а не всем сезоном одним скопом.
        В исходных данных есть игровые дни, победы и ничьи команд, но нет явных поражений.
        Поэтому количество игр команды за день восстанавливается расчетно по логике ротации команд:
        победитель остается, проигравший садится; при ничьей для 3 команд садится команда с большей текущей серией игр,
        для 4+ команд садятся обе команды.
        """
    )

    if efficiency.empty:
        st.info("Недостаточно данных для аналитики.")
        return

    st.subheader("Индекс эффективности игроков")
    full_dataframe(efficiency, height=420)

    st.subheader("Предпочтительные партнеры")
    names = sorted(scope_stats["player_name"].dropna().unique())
    player_name = st.selectbox("Выберите игрока для анализа связок:", names)

    partners = calculate_partners(scope_stats, scope_teams, player_name, rules=partners_rules, rule=partners_rule)
    st.markdown(
        """
        **Формула индекса связки:**  
        `Индекс связки = 0.5 × частота совместных игр + 0.5 × результативность пары`  
        `частота = игр вместе / максимум игр вместе среди партнеров`  
        `результативность пары = очки пары за игру / лучший показатель среди партнеров`
        """
    )
    if partners.empty:
        st.info("Для выбранного игрока не найдено партнеров в одной команде.")
    else:
        full_dataframe(partners, height=360)

    st.subheader("Короткие выводы")
    best_player = efficiency.iloc[0]
    st.write(
        "Лучший индекс в выбранном периоде: **{}** — **{}**.".format(
            best_player["Игрок"], best_player["Индекс"]
        )
    )
    if not partners.empty:
        best_partner = partners.iloc[0]
        st.write(
            "Самая сильная связка для **{}**: **{}**, индекс связки — **{}**.".format(
                player_name, best_partner["Партнер"], best_partner["Индекс связки"]
            )
        )

def show_home(rules: pd.DataFrame, stats: pd.DataFrame, teams: pd.DataFrame):
    st.title("Футбол в МИТИНО")
    st.header('Сводная статистика по сезонам')

    rows = []
    for rule in rules.sort_values(["start", "tournament_name"], ascending=[False, True]).itertuples():
        rule_series = get_tournament_rules(rules, int(rule.tournament_id))
        stats_filtered, teams_filtered = filter_by_tournament(stats, teams, rule_series)
        summary = season_summary(stats_filtered, teams_filtered)
        rows.append({
            "Площадка": rule.tournament_name,
            "Сезон": rule.season,
            "Старт": rule.start.strftime("%d.%m.%Y") if pd.notna(rule.start) else "",
            "Финиш": rule.end.strftime("%d.%m.%Y") if pd.notna(rule.end) else "",
            "Игр сыграно": summary["games"],
        })

    centered_dataframe(pd.DataFrame(rows), height=300, width=900)
    st.markdown('<div class="footer">© MitinoSarayTeam</div>', unsafe_allow_html=True)

def show_summary(rule: pd.Series, stats_filtered: pd.DataFrame, teams_filtered: pd.DataFrame):
    summary = season_summary(stats_filtered, teams_filtered)
    title = tournament_title(rule)

    st.markdown(
        f"""
        <div class="classic-summary">
            <h1>{title}</h1>
            <div class="line">Игр сыграно: {summary['games']} (из них ничьи: {summary['draws']})</div>
            <div class="line">Голов забито: {summary['goals']}</div>
            <div class="line">Пасов отдано: {summary['assists']}</div>
            <div class="line">Shutout: {summary['saves']}</div>
            <div class="line">Фолов: {summary['fouls']}</div>
            <div class="footer-left">© MitinoSarayTeam</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="rules-box">', unsafe_allow_html=True)
    with st.expander("Правила начисления очков"):
        rules_table = pd.DataFrame({
            "Показатель": ["Гол", "Пас", "Победа", "Ничья", "На ноль", "Фол"],
            "Коэффициент": [
                rule["goals_coefficient"],
                rule["assists_coefficient"],
                rule["wins_coefficient"],
                rule["draws_coefficient"],
                rule["saves_coefficient"],
                rule["foul_coefficient"],
            ],
        })
        centered_dataframe(rules_table, height=245, width=360)
    st.markdown('</div>', unsafe_allow_html=True)

def show_top(players_stats: pd.DataFrame, rule: pd.Series):
    st.title(tournament_title(rule))
    if players_stats.empty:
        st.info("За этот турнир пока нет статистики.")
        return

    for title, column, label in TOP_TABLES:
        if column not in players_stats.columns:
            continue
        st.subheader(title)
        table = players_stats[["player_name", column]].sort_values(column, ascending=False)
        table = table.rename(columns={"player_name": "Игрок", column: label})
        centered_dataframe(table, height=220, width=420)


def show_games_by_date(stats_filtered: pd.DataFrame, rule: pd.Series):
    st.title(tournament_title(rule))
    st.subheader("Статистика игр по датам")
    if stats_filtered.empty:
        st.info("За этот турнир пока нет статистики.")
        return

    available_dates = sorted(stats_filtered["date"].dropna().dt.date.unique())
    date_filter = st.selectbox("Выберите дату:", available_dates, index=len(available_dates) - 1)

    table = stats_filtered[stats_filtered["date"].dt.date == date_filter].copy()
    table = add_points(table, rule)
    table["date"] = table["date"].dt.strftime("%d.%m.%Y")

    columns = [c for c in DISPLAY_COLUMNS if c in table.columns]
    table = table[columns].rename(columns=DISPLAY_COLUMNS)
    full_dataframe(table, height=620)


def show_personal_stats(players_stats: pd.DataFrame, stats_filtered: pd.DataFrame, rule: pd.Series):
    st.title(tournament_title(rule))
    if players_stats.empty or stats_filtered.empty:
        st.info("За этот турнир пока нет статистики.")
        return

    names = sorted(players_stats["player_name"].dropna().unique())
    player_name = st.selectbox("Выберите игрока:", names)
    comparison_player_name = st.selectbox("Выберите игрока для сравнения:", names)

    player_stats = stats_filtered[stats_filtered["player_name"] == player_name].copy()
    comparison_stats = stats_filtered[stats_filtered["player_name"] == comparison_player_name].copy()

    def totals(df: pd.DataFrame) -> Dict[str, float]:
        unique_days = max(df["date"].dt.date.nunique(), 1)
        return {
            "goals": df["goals_on_date"].sum(),
            "assists": df["assists_on_date"].sum(),
            "wins": df["wins_on_date"].sum(),
            "draws": df["draws_on_date"].sum(),
            "saves": df["saves_on_date"].sum(),
            "foul": df["foul_on_date"].sum(),
            "days": unique_days,
        }

    player_total = totals(player_stats)
    comparison_total = totals(comparison_stats)

    st.subheader("Статистика по игроку: {}".format(player_name))
    st.write(
        "Побед: {} | Ничьих: {} | Голов: {} | Пасов: {} | На ноль: {} | Фолов: {}".format(
            int(player_total["wins"]), int(player_total["draws"]), int(player_total["goals"]),
            int(player_total["assists"]), int(player_total["saves"]), int(player_total["foul"])
        )
    )

    table = add_points(player_stats, rule)
    table["date"] = table["date"].dt.strftime("%d.%m.%Y")
    personal_columns = [c for c in DISPLAY_COLUMNS if c in table.columns and c != "player_name"]
    full_dataframe(table[personal_columns].rename(columns=DISPLAY_COLUMNS), height=300)

    radar_categories = ["goals", "assists", "wins", "draws", "saves", "foul"]
    labels = ["голы", "пасы", "победы", "ничьи", "на ноль", "фолы"]
    player_val = [player_total[x] / player_total["days"] for x in radar_categories]
    comparison_val = [comparison_total[x] / comparison_total["days"] for x in radar_categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=player_val,
        theta=labels,
        fill="toself",
        name=player_name,
        line=dict(color="red", width=3),
        fillcolor="rgba(255, 0, 0, 0.25)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=comparison_val,
        theta=labels,
        fill="toself",
        name=comparison_player_name,
        line=dict(color="gold", width=3),
        fillcolor="rgba(255, 215, 0, 0.25)",
    ))
    fig.update_layout(
        title={"text": "Пятиугольник силы", "x": 0.5},
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
        height=520,
        margin=dict(l=30, r=30, t=70, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def main():
    players, stats, teams, rules = load_data()

    main_section = st.sidebar.radio(
        "Меню:",
        ["Главная", "Аналитика", "Турниры"]
    )

    if main_section == "Главная":
        show_home(rules, stats, teams)
        return

    if main_section == "Аналитика":
        show_analytics(stats, teams, rules)
        return

    selected_tournament = st.sidebar.radio(
        "Турнир:",
        sorted(rules["tournament_name"].dropna().unique().tolist())
    )

    place_rules = rules[rules["tournament_name"] == selected_tournament].sort_values("start", ascending=False)
    label_to_id = {}
    for row in place_rules.itertuples():
        label = season_label(row)
        if label in label_to_id:
            label = "{} ({})".format(label, int(row.tournament_id))
        label_to_id[label] = int(row.tournament_id)

    selected = st.sidebar.radio("Сезон:", list(label_to_id.keys()))
    tournament_id = label_to_id[selected]
    rule = get_tournament_rules(rules, tournament_id)

    section = st.sidebar.radio("Раздел:", ["Главная", "Топ", "Общая стат.", "Личная стат."])
    stats_filtered, teams_filtered = filter_by_tournament(stats, teams, rule)
    players_stats = aggregate_players(stats_filtered, rule)

    if section == "Главная":
        show_summary(rule, stats_filtered, teams_filtered)
    elif section == "Топ":
        show_top(players_stats, rule)
    elif section == "Общая стат.":
        show_games_by_date(stats_filtered, rule)
    elif section == "Личная стат.":
        show_personal_stats(players_stats, stats_filtered, rule)


if __name__ == "__main__":
    main()
