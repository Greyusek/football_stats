# Football Stats APP
Simple football stats streamlit (python) info page

# START LOCAL SERVER

## expand the virtual environment
python -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r reqirements.txt

## run server
python -m streamlit run main.py

## now you can view your Streamlit app in your browser:

Local URL: http://localhost:8501
Network URL: http://192.168.0.22:8501

# XLSX vs CSV
The application runs on the free streamlit server.
Since it does not support processing excle files and the openpyxl library,
I put a converter file in the repository that creates three files in csv format from the football_stats.xlsx file:
players.csv, stats.csv and teams.csv

### sclerosis
git pull origin main