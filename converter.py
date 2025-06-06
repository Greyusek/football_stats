import pandas as pd
def convert_excel_to_csv(excel_file):
    # Загружаем Excel файл
    xls = pd.ExcelFile(excel_file)
    
    # Читаем данные из каждого листа
    players_df = pd.read_excel(xls, sheet_name='Players')
    stats_df = pd.read_excel(xls, sheet_name='Stats')
    teams_df = pd.read_excel(xls, sheet_name='Teams')
    
    # Сохраняем данные в CSV файлы
    players_df.to_csv('players.csv', index=False, encoding='utf-8')
    stats_df.to_csv('stats.csv', index=False, encoding='utf-8')
    teams_df.to_csv('teams.csv', index=False, encoding='utf-8')
    print("Файлы успешно сохранены: players.csv, stats.csv, teams.csv")
# Укажите имя вашего Excel файла
convert_excel_to_csv('football_stats.xlsx')