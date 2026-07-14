НОВЫЙ РАЗДЕЛ «ДОСТИЖЕНИЯ»

1. Заполните лист Achievements:
   achievement_id   — уникальный числовой ID достижения;
   achievement_name — название;
   description      — описание;
   image_path       — путь к картинке, например achievement_pic/1.png.

2. Заполните лист Hall_of_Fame:
   player_id        — ID игрока строго как в листе Players;
   achievement_id   — ID достижения из листа Achievements;
   date             — дата получения;
   proof_link       — полная ссылка на YouTube, Google Drive и т.п.

3. Запустите:
   python converter.py

Будут созданы achievements.csv и hall_of_fame.csv вместе с остальными CSV.

4. Запустите сайт:
   streamlit run main.py

В меню появится раздел «Достижения». Кнопка «Открыть достижение» ведет
на отдельное состояние страницы с URL-параметром ?achievement=ID.
