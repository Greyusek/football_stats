import streamlit as st
import pandas as pd

def load_data():
    xls = pd.ExcelFile('football_stats.xlsx')
    players_df = pd.read_excel(xls, sheet_name='Players')
    stats_df = pd.read_excel(xls, sheet_name='Stats')
    teams_df = pd.read_excel(xls, sheet_name='Teams')
    players_df = players_df.drop(columns=['player_id'], errors='ignore')
    stats_df = stats_df.drop(columns=['player_id'], errors='ignore')
    players_df['player_name'] = players_df['player_name'].fillna("Неизвестно")
    players_df['player_name'] = players_df['player_name'].astype(str)
    if 'date' in stats_df.columns:
        stats_df['date'] = pd.to_datetime(stats_df['date']).dt.strftime('%d.%m.%y')
    return players_df, stats_df, teams_df

st.title('Лето 2025')
players_df, stats_df, teams_df = load_data()
menu = st.sidebar.radio("Меню:", ("Главная", "Топ", "Общая стат.", "Личная стат."))
if menu == "Главная":
    total_games = teams_df['wins_on_date'].sum()
    total_goals = stats_df['goals_on_date'].sum()
    total_assists = stats_df['assists_on_date'].sum()
    st.subheader(f"Игр сыграно: {total_games}")
    st.subheader(f"Голов забито: {total_goals}")
    st.subheader(f"Пасов отдано: {total_assists}")
    st.write("© MitinoSarayTeam")
elif menu == "Топ":
    points_df = players_df[['player_name', 'points']].sort_values(by='points', ascending=False)
    points_df = points_df.rename(columns={'player_name': 'Игрок', 'points': 'Очки'})
    st.subheader('Общий рейтинг')
    st.dataframe(points_df, hide_index=True, height=200, width=400)
    goals_df = players_df[['player_name', 'goals']].sort_values(by='goals', ascending=False)
    goals_df = goals_df.rename(columns={'player_name': 'Игрок', 'goals': 'Голы'})
    st.subheader('Топ бомбардиров')
    st.dataframe(goals_df, hide_index=True, height=200, width=400)
    assists_df = players_df[['player_name', 'assists']].sort_values(by='assists', ascending=False)
    assists_df = assists_df.rename(columns={'player_name': 'Игрок', 'assists': 'Пасы'})
    st.subheader('Топ раздающих')
    st.dataframe(assists_df, hide_index=True, height=200, width=400)
    points_df = players_df[['player_name', 'wins']].sort_values(by='wins', ascending=False)
    points_df = points_df.rename(columns={'player_name': 'Игрок', 'wins': 'Побед'})
    st.subheader('Количество побед')
    st.dataframe(points_df, hide_index=True, height=200, width=400)

elif menu == "Общая стат.":
    st.subheader('Статистика игр по датам')
    date_filter = st.date_input("Выберите дату:", value=pd.to_datetime('today'))
    date_filter_str = date_filter.strftime('%d.%m.%y')
    filtered_stats_df = stats_df[stats_df['date'] == date_filter_str]
    filtered_stats_df = filtered_stats_df.rename(columns={
        'date': 'Число',
        'team_number': '№ команды',
        'player_name': 'Игрок',
        'goals_on_date': 'Голы',
        'assists_on_date': 'Пасы',
        'wins_on_date': 'Победы',
    })
    filtered_stats_df['Очки'] = filtered_stats_df['Голы'] + filtered_stats_df['Пасы'] + filtered_stats_df['Победы']
    st.dataframe(filtered_stats_df, use_container_width=True, hide_index=True, height=750)
elif menu == "Личная стат.":
    player_name = st.selectbox("Выберите игрока:", players_df['player_name'].unique())
    player_stats = stats_df[stats_df['player_name'] == player_name]
    if not player_stats.empty:
        player_stats = player_stats.drop(columns=['player_name'])
        player_stats = player_stats.rename(columns={
            'date': 'Число',
            'player_name': 'Игрок',
            'team_number': '№ команды',
            'goals_on_date': 'Голы',
            'assists_on_date': 'Пасы',
            'wins_on_date': 'Победы'
        })
        st.subheader(f'Статистика по игроку: {player_name}')
        total_goals = player_stats['Голы'].sum()
        total_games = player_stats['Победы'].sum()
        total_assists = player_stats['Пасы'].sum()
        st.write(f"Побед: {total_games} Голов: {total_goals} Пасов: {total_assists}")      
        st.dataframe(player_stats, use_container_width=True, hide_index=True)
    else:
        st.write("Нет данных для выбранного игрока.")
