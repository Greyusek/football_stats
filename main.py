import streamlit as st
import pandas as pd
import plotly.express as px

SUMMER2025 = ['2025-05-29', '2025-08-31']
AUTUMN2025 = ['2025-09-01', '2025-11-30']
UPK = 'УПК'
BARISHIHA = 'Барышиха'

def load_data():
    players_df = pd.read_csv('players.csv')
    stats_df = pd.read_csv('stats.csv')
    teams_df = pd.read_csv('teams.csv')
    players_df = players_df.drop(columns=['player_id'], errors='ignore')
    stats_df = stats_df.drop(columns=['player_id'], errors='ignore')
    players_df['player_name'] = players_df['player_name'].fillna("Неизвестно")
    players_df['player_name'] = players_df['player_name'].astype(str)
    if 'date' in stats_df.columns:
        stats_df['date'] = pd.to_datetime(stats_df['date']).dt.strftime('%d.%m.%y')
    return players_df, stats_df, teams_df

def radar_chart(val, comparison_val, player_name, comparison_player_name):  
    df = pd.DataFrame(dict(
        r=val,
        theta=['голы', 'пасы', 'победы','ничьи', 'на ноль']))
    dfa = pd.DataFrame(dict(
        r=comparison_val,
        theta=['голы', 'пасы', 'победы', 'ничьи', 'на ноль']))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True, title="Пятиугольник силы")
    fig.add_scatterpolar(r=df['r'], theta=df['theta'], fill='toself', name=player_name, line=dict(color='red'))
    fig.add_scatterpolar(r=dfa['r'], theta=dfa['theta'], fill='toself', name=comparison_player_name, line=dict(color='orange'))
    st.write(fig)

def season_filter_players_stats(season, rules, tournament):
    start_date = pd.to_datetime(season[0])
    end_date = pd.to_datetime(season[1])
    stats_df = pd.read_csv('stats.csv')
    stats_df['date'] = pd.to_datetime(stats_df['date'], errors='coerce')
    filtered_df = stats_df[(stats_df['date'] >= start_date) & (stats_df['date'] <= end_date)]
    filtered_df = filtered_df[filtered_df['tournament'] == tournament]
    aggregated_stats = filtered_df.groupby(['player_id', 'player_name'], as_index=False).agg({
        'goals_on_date': 'sum',
        'assists_on_date': 'sum',
        'wins_on_date': 'sum',
        'saves_on_date': 'sum',
        'draws_on_date': 'sum'
    })
    aggregated_stats = aggregated_stats.rename(columns={
        'goals_on_date': 'goals',
        'assists_on_date': 'assists',
        'wins_on_date': 'wins',
        'saves_on_date': 'saves',
        'draws_on_date': 'draws'
    })
    aggregated_stats['points'] = (aggregated_stats['goals'] +
                              aggregated_stats['assists'] +
                              aggregated_stats['wins']*rules +
                              aggregated_stats['saves'] +
                              aggregated_stats['draws'])
    return aggregated_stats

def season_filter(season, tournament):
    start_date = pd.to_datetime(season[0])
    end_date = pd.to_datetime(season[1])
    
    teams_df = pd.read_csv('teams.csv')

    teams_df['date'] = pd.to_datetime(teams_df['date'], errors='coerce')
    mask = (teams_df['date'] >= start_date) & (teams_df['date'] <= end_date)
    filtered_teams = teams_df.loc[mask]
    filtered_teams = filtered_teams[filtered_teams['tournament'] == tournament]
    total_wins = int(filtered_teams['wins_on_date'].sum()) 
    total_draws = int(filtered_teams['draws_on_date'].sum()/2)
    total_games = total_wins + total_draws
    
    stats_df = pd.read_csv('stats.csv')

    stats_df['date'] = pd.to_datetime(stats_df['date'], errors='coerce')
    mask = (stats_df['date'] >= start_date) & (stats_df['date'] <= end_date)
    filtered_stats = stats_df.loc[mask]
    filtered_stats = filtered_stats[filtered_stats['tournament'] == tournament]
    total_goals = int(filtered_stats['goals_on_date'].sum())
    total_assists = int(filtered_stats['assists_on_date'].sum())
    total_saves = int(filtered_stats['saves_on_date'].sum())

    return total_games, total_draws, total_goals, total_assists, total_saves

def season_filter_stats(season, tournament):
    start_date = pd.to_datetime(season[0])
    end_date = pd.to_datetime(season[1])
    df = pd.read_csv('stats.csv')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    filtered_df = df.loc[mask]
    filtered_df = filtered_df[filtered_df['tournament'] == tournament]
    return filtered_df

players_df, stats_df, teams_df = load_data()
menu = st.sidebar.radio("Меню:", ("Главная", "Барышиха", "УПК"))
if menu == "Главная":
    st.title('Футбол в МИТИНО')
    st.header('Сезон "Осень 2025" - Барышиха/УПК')
if menu == "Барышиха":
    sub_menu = st.sidebar.radio("Барышиха:", ("Главная", "Топ", "Общая стат.", "Личная стат.", "Архив"))
    if sub_menu == "Главная":
        st.title('Осень 2025 (БАРЫШИХА)')
        total_games, total_draws, total_goals, total_assists, total_saves = season_filter(AUTUMN2025, BARISHIHA)
        st.subheader(f"Игр сыграно: {total_games} (из них ничьи: {total_draws})")
        st.subheader(f"Голов забито: {total_goals}")
        st.subheader(f"Пасов отдано: {total_assists}")
        st.subheader(f"Shutout: {total_saves}")
        st.subheader("Рыжий не пришел на футбол: 1")
        st.write("© MitinoSarayTeam")
    elif sub_menu == "Топ":
        st.title('Осень 2025 (БАРЫШИХА)')
        players_df = season_filter_players_stats(AUTUMN2025, 2, BARISHIHA)
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
        points_df = players_df[['player_name', 'saves']].sort_values(by='saves', ascending=False)
        points_df = points_df.rename(columns={'player_name': 'Игрок', 'saves': 'Отстоял на ноль'})
        st.subheader('Топ голкиперов')
        st.dataframe(points_df, hide_index=True, height=200, width=400)    
        points_df = players_df[['player_name', 'wins']].sort_values(by='wins', ascending=False)
        points_df = points_df.rename(columns={'player_name': 'Игрок', 'wins': 'Побед'})
        st.subheader('Количество побед')
        st.dataframe(points_df, hide_index=True, height=200, width=400)
        points_df = players_df[['player_name', 'draws']].sort_values(by='draws', ascending=False)
        points_df = points_df.rename(columns={'player_name': 'Игрок', 'draws': 'Ничьих'})
        st.subheader('Количество ничьих')
        st.dataframe(points_df, hide_index=True, height=200, width=400)
    elif sub_menu == "Общая стат.":
        st.title('Осень 2025 (БАРЫШИХА)')
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
            'saves_on_date': 'Отстоял на ноль',
            'wins_on_date': 'Победы',
            'draws_on_date': 'Ничьи'
        })
        filtered_stats_df['Очки'] = filtered_stats_df['Голы'] + filtered_stats_df['Пасы'] + filtered_stats_df['Победы']*2 + filtered_stats_df['Отстоял на ноль'] + filtered_stats_df['Ничьи']
        st.dataframe(filtered_stats_df, use_container_width=True, hide_index=True, height=750)
    elif sub_menu == "Личная стат.":
        st.title('Осень 2025 (БАРЫШИХА)')
        players_df = season_filter_players_stats(AUTUMN2025, 2, BARISHIHA)
        stats_df = season_filter_stats(AUTUMN2025, BARISHIHA)

        player_name = st.selectbox("Выберите игрока:", players_df['player_name'].unique())
        comparison_player_name = st.selectbox("Выберите игрока для сравнения:", players_df['player_name'].unique())
        player_stats = stats_df[stats_df['player_name'] == player_name]
        comparison_player_stats = stats_df[stats_df['player_name'] == comparison_player_name]  
        if not player_stats.empty and not comparison_player_stats.empty:
            player_stats = player_stats.drop(columns=['player_id', 'player_name'])
            player_stats = player_stats.rename(columns={
                'date': 'Число',
                'team_number': '№ команды',
                'goals_on_date': 'Голы',
                'assists_on_date': 'Пасы',
                'saves_on_date': 'Отстоял на ноль',
                'wins_on_date': 'Победы',
                'draws_on_date': 'Ничьи'
            })
            player_stats['Число'] = pd.to_datetime(player_stats['Число']).dt.strftime('%d.%m.%Y')

            st.subheader(f'Статистика по игроку: {player_name}')
        
            unique_days = player_stats['Число'].nunique()

            total_goals = player_stats['Голы'].sum()
            total_games = player_stats['Победы'].sum()
            total_draws = player_stats['Ничьи'].sum()
            total_assists = player_stats['Пасы'].sum()
            total_saves = player_stats['Отстоял на ноль'].sum()

            player_val = [total_goals/unique_days, total_assists/unique_days, total_games/unique_days, total_draws/unique_days, total_saves/unique_days]
        
            st.write(f"Побед: {total_games} Ничьих {total_draws} Голов: {total_goals} Пасов: {total_assists} Отстоял на ноль: {total_saves}")
            st.dataframe(player_stats, use_container_width=True, hide_index=True)
            comparison_player_stats = comparison_player_stats.drop(columns=['player_id', 'player_name'])
            comparison_player_stats = comparison_player_stats.rename(columns={
                'date': 'Число',
                'team_number': '№ команды',
                'goals_on_date': 'Голы',
                'assists_on_date': 'Пасы',
                'saves_on_date': 'Отстоял на ноль',
                'wins_on_date': 'Победы',
                'draws_on_date': 'Ничьи'

            })
            comparison_player_stats['Число'] = pd.to_datetime(comparison_player_stats['Число']).dt.strftime('%d.%m.%Y')
        
            comparison_unique_days = comparison_player_stats['Число'].nunique()

            comparison_total_goals = comparison_player_stats['Голы'].sum()
            comparison_total_games = comparison_player_stats['Победы'].sum()
            comparison_total_draws = comparison_player_stats['Ничьи'].sum()
            comparison_total_assists = comparison_player_stats['Пасы'].sum()
            comparison_total_saves = comparison_player_stats['Отстоял на ноль'].sum()
            comparison_val = [comparison_total_goals/comparison_unique_days,
                            comparison_total_assists/comparison_unique_days,
                            comparison_total_games/comparison_unique_days,
                            comparison_total_draws/comparison_unique_days,
                            comparison_total_saves/comparison_unique_days]
                          
        
            radar_chart(player_val, comparison_val, player_name, comparison_player_name)
        else:
            st.write("Нет данных для одного или обоих выбранных игроков.")
    elif sub_menu == "Архив":
        stat_submenu = st.sidebar.radio("Архив данных:", ("Лето 2025"))
        if stat_submenu == "Лето 2025":
            st.title('Лето 2025')
            player_submenu = st.sidebar.radio("Статистика за лето 2025:", ("Главная", "Топ", "Общая стат.", "Личная стат."))
            if player_submenu == "Главная":
                total_games, total_draws, total_goals, total_assists, total_saves = season_filter(SUMMER2025, BARISHIHA)
                st.subheader(f"Игр сыграно: {total_games}")
                st.subheader(f"Голов забито: {total_goals}")
                st.subheader(f"Пасов отдано: {total_assists}")
                st.subheader("Рыжий пришел на футбол: 2")
                st.write("© MitinoSarayTeam")
            elif player_submenu == "Топ":
                players_df = season_filter_players_stats(SUMMER2025, 1, BARISHIHA)
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
            elif player_submenu == "Общая стат.":
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
                    'saves_on_date': 'Отстоял на ноль',
                    'wins_on_date': 'Победы',
                    'draws_on_date': 'Ничьи'
                })
                filtered_stats_df['Очки'] = filtered_stats_df['Голы'] + filtered_stats_df['Пасы'] + filtered_stats_df['Победы']*2 + filtered_stats_df['Отстоял на ноль'] + filtered_stats_df['Ничьи']
                st.dataframe(filtered_stats_df, use_container_width=True, hide_index=True, height=750)
            elif player_submenu == "Личная стат.":
                players_df = season_filter_players_stats(SUMMER2025, 2, BARISHIHA)
                stats_df = season_filter_stats(SUMMER2025, BARISHIHA)
                player_name = st.selectbox("Выберите игрока:", players_df['player_name'].unique())
                comparison_player_name = st.selectbox("Выберите игрока для сравнения:", players_df['player_name'].unique())
                player_stats = stats_df[stats_df['player_name'] == player_name]
                comparison_player_stats = stats_df[stats_df['player_name'] == comparison_player_name]  
                if not player_stats.empty and not comparison_player_stats.empty:
                    player_stats = player_stats.drop(columns=['player_id', 'player_name'])
                    player_stats = player_stats.rename(columns={
                        'date': 'Число',
                        'team_number': '№ команды',
                        'goals_on_date': 'Голы',
                        'assists_on_date': 'Пасы',
                        'saves_on_date': 'Отстоял на ноль',
                        'wins_on_date': 'Победы',
                        'draws_on_date': 'Ничьи'
                    })
                    player_stats['Число'] = pd.to_datetime(player_stats['Число']).dt.strftime('%d.%m.%Y')
                
                    st.subheader(f'Статистика по игроку: {player_name}')
        
                    unique_days = player_stats['Число'].nunique()

                    total_goals = player_stats['Голы'].sum()
                    total_games = player_stats['Победы'].sum()
                    total_draws = player_stats['Ничьи'].sum()
                    total_assists = player_stats['Пасы'].sum()
                    total_saves = player_stats['Отстоял на ноль'].sum()

                    player_val = [total_goals/unique_days, total_assists/unique_days, total_games/unique_days, total_draws/unique_days, total_saves/unique_days]
        
                    st.write(f"Побед: {total_games} Ничьих: {total_draws} Голов: {total_goals} Пасов: {total_assists} Отстоял на ноль: {total_saves}")
                    st.dataframe(player_stats, use_container_width=True, hide_index=True)
                    comparison_player_stats = comparison_player_stats.drop(columns=['player_id', 'player_name'])
                    comparison_player_stats = comparison_player_stats.rename(columns={
                        'date': 'Число',
                        'team_number': '№ команды',
                        'goals_on_date': 'Голы',
                        'assists_on_date': 'Пасы',
                        'saves_on_date': 'Отстоял на ноль',
                        'wins_on_date': 'Победы',
                        'draws_on_date': 'Ничьи'
                    })
                    comparison_player_stats['Число'] = pd.to_datetime(comparison_player_stats['Число']).dt.strftime('%d.%m.%Y')

                    comparison_unique_days = comparison_player_stats['Число'].nunique()

                    comparison_total_goals = comparison_player_stats['Голы'].sum()
                    comparison_total_games = comparison_player_stats['Победы'].sum()
                    comparison_total_draws = comparison_player_stats['Ничьи'].sum()
                    comparison_total_assists = comparison_player_stats['Пасы'].sum()
                    comparison_total_saves = comparison_player_stats['Отстоял на ноль'].sum()
                    comparison_val = [comparison_total_goals/comparison_unique_days,
                                    comparison_total_assists/comparison_unique_days,
                                    comparison_total_games/comparison_unique_days,
                                    comparison_total_draws/comparison_unique_days,
                                    comparison_total_saves/comparison_unique_days]
        
                    radar_chart(player_val, comparison_val, player_name, comparison_player_name)
                else:
                    st.write("Нет данных для одного или обоих выбранных игроков.")
if menu == "УПК":
    sub_menu = st.sidebar.radio("УПК:", ("Главная", "Топ", "Общая стат.", "Личная стат."))
    if sub_menu == "Главная":
        st.title('Осень 2025 (УПК)')
        total_games, total_draws, total_goals, total_assists, total_saves = season_filter(AUTUMN2025, UPK)
        st.subheader(f"Игр сыграно: {total_games} (из них ничьи: {total_draws})")
        st.subheader(f"Голов забито: {total_goals}")
        st.subheader(f"Пасов отдано: {total_assists}")
        st.subheader(f"Shutout: {total_saves}")
        st.subheader("Рыжий не пришел на футбол: 1")
        st.write("© MitinoSarayTeam")
    elif sub_menu == "Топ":
        st.title('Осень 2025 (УПК)')
        players_df = season_filter_players_stats(AUTUMN2025, 2, UPK)
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
        points_df = players_df[['player_name', 'saves']].sort_values(by='saves', ascending=False)
        points_df = points_df.rename(columns={'player_name': 'Игрок', 'saves': 'Отстоял на ноль'})
        st.subheader('Топ голкиперов')
        st.dataframe(points_df, hide_index=True, height=200, width=400)    
        points_df = players_df[['player_name', 'wins']].sort_values(by='wins', ascending=False)
        points_df = points_df.rename(columns={'player_name': 'Игрок', 'wins': 'Побед'})
        st.subheader('Количество побед')
        st.dataframe(points_df, hide_index=True, height=200, width=400)
        points_df = players_df[['player_name', 'draws']].sort_values(by='draws', ascending=False)
        points_df = points_df.rename(columns={'player_name': 'Игрок', 'draws': 'Ничьих'})
        st.subheader('Количество ничьих')
        st.dataframe(points_df, hide_index=True, height=200, width=400)
    elif sub_menu == "Общая стат.":
        st.title('Осень 2025 (УПК)')
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
            'saves_on_date': 'Отстоял на ноль',
            'wins_on_date': 'Победы',
            'draws_on_date': 'Ничьи'
        })
        filtered_stats_df['Очки'] = filtered_stats_df['Голы'] + filtered_stats_df['Пасы'] + filtered_stats_df['Победы']*2 + filtered_stats_df['Отстоял на ноль'] + filtered_stats_df['Ничьи']
        st.dataframe(filtered_stats_df, use_container_width=True, hide_index=True, height=750)
    elif sub_menu == "Личная стат.":
        st.title('Осень 2025 (УПК)')
        players_df = season_filter_players_stats(AUTUMN2025, 2, UPK)
        stats_df = season_filter_stats(AUTUMN2025, UPK)

        player_name = st.selectbox("Выберите игрока:", players_df['player_name'].unique())
        comparison_player_name = st.selectbox("Выберите игрока для сравнения:", players_df['player_name'].unique())
        player_stats = stats_df[stats_df['player_name'] == player_name]
        comparison_player_stats = stats_df[stats_df['player_name'] == comparison_player_name]  
        if not player_stats.empty and not comparison_player_stats.empty:
            player_stats = player_stats.drop(columns=['player_id', 'player_name'])
            player_stats = player_stats.rename(columns={
                'date': 'Число',
                'team_number': '№ команды',
                'goals_on_date': 'Голы',
                'assists_on_date': 'Пасы',
                'saves_on_date': 'Отстоял на ноль',
                'wins_on_date': 'Победы',
                'draws_on_date': 'Ничьи'
            })
            player_stats['Число'] = pd.to_datetime(player_stats['Число']).dt.strftime('%d.%m.%Y')

            st.subheader(f'Статистика по игроку: {player_name}')
        
            unique_days = player_stats['Число'].nunique()

            total_goals = player_stats['Голы'].sum()
            total_games = player_stats['Победы'].sum()
            total_draws = player_stats['Ничьи'].sum()
            total_assists = player_stats['Пасы'].sum()
            total_saves = player_stats['Отстоял на ноль'].sum()

            player_val = [total_goals/unique_days, total_assists/unique_days, total_games/unique_days, total_draws/unique_days, total_saves/unique_days]
        
            st.write(f"Побед: {total_games} Ничьих {total_draws} Голов: {total_goals} Пасов: {total_assists} Отстоял на ноль: {total_saves}")
            st.dataframe(player_stats, use_container_width=True, hide_index=True)
            comparison_player_stats = comparison_player_stats.drop(columns=['player_id', 'player_name'])
            comparison_player_stats = comparison_player_stats.rename(columns={
                'date': 'Число',
                'team_number': '№ команды',
                'goals_on_date': 'Голы',
                'assists_on_date': 'Пасы',
                'saves_on_date': 'Отстоял на ноль',
                'wins_on_date': 'Победы',
                'draws_on_date': 'Ничьи'

            })
            comparison_player_stats['Число'] = pd.to_datetime(comparison_player_stats['Число']).dt.strftime('%d.%m.%Y')
        
            comparison_unique_days = comparison_player_stats['Число'].nunique()

            comparison_total_goals = comparison_player_stats['Голы'].sum()
            comparison_total_games = comparison_player_stats['Победы'].sum()
            comparison_total_draws = comparison_player_stats['Ничьи'].sum()
            comparison_total_assists = comparison_player_stats['Пасы'].sum()
            comparison_total_saves = comparison_player_stats['Отстоял на ноль'].sum()
            comparison_val = [comparison_total_goals/comparison_unique_days,
                            comparison_total_assists/comparison_unique_days,
                            comparison_total_games/comparison_unique_days,
                            comparison_total_draws/comparison_unique_days,
                            comparison_total_saves/comparison_unique_days]
                          
        
            radar_chart(player_val, comparison_val, player_name, comparison_player_name)
        else:
            st.write("Нет данных для одного или обоих выбранных игроков.")