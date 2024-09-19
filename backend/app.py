from flask import Flask, jsonify, request
import requests
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)

# In-memory storage for the latest weather and last fetched date
latest_weather = {}
last_fetched_date = None  # Track the last fetched date for history

# Database setup
def init_db():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS temperatures (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        temperature REAL,
                        timestamp TEXT
                    )''')
    conn.commit()
    conn.close()

# Function to fetch weather data from the API and update in-memory storage
def fetch_weather():
    global latest_weather
    check_date = datetime.today().strftime('%Y-%m-%d')
    url = f"https://api.open-meteo.com/v1/forecast?latitude=40.71&longitude=-74.01&hourly=temperature_2m&start_date={check_date}&end_date={check_date}&timezone=America%2FNew_York"
    response = requests.get(url)
    data = response.json()
    # Get current temperature and timestamp
    latest_weather['temperature'] = data['hourly']['temperature_2m'][-1]
    latest_weather['timestamp'] = data['hourly']['time'][-1]

# Function to schedule auto-updating weather every 60 seconds
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_weather, 'interval', seconds=60)  # Update every 60 seconds
    scheduler.start()

# Route to return current weather (from in-memory storage)
@app.route('/weather', methods=['GET'])
def get_weather():
    return jsonify(latest_weather)

# Route to return weather history (last 5 days' average temperature)
@app.route('/history', methods=['GET'])
def get_weather_history():
    global last_fetched_date

    current_date = datetime.today().strftime('%Y-%m-%d')

    # If it's a new day or this is the first request, fetch new history
    if 1:
        history_date = (datetime.today() - timedelta(days=5)).strftime('%Y-%m-%d')
        previous_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        url = f"https://api.open-meteo.com/v1/forecast?latitude=40.71&longitude=-74.01&hourly=temperature_2m&start_date={history_date}&end_date={previous_date}&timezone=America%2FNew_York"
        response = requests.get(url)
        data = response.json()

        # Process temperature data to get daily averages
        temperatures = data['hourly']['temperature_2m']
        timestamps = data['hourly']['time']
        timestamp_format = "%Y-%m-%dT%H:%M"

        date_temp = []
        avg_temp_daily = []
        sum_daily_temp = float(temperatures[0])
        times_measured_daily = 1

        for i in range(1, len(timestamps)):
            current_date_entry = datetime.strptime(timestamps[i], timestamp_format).strftime('%Y-%m-%d')
            previous_date_entry = datetime.strptime(timestamps[i-1], timestamp_format).strftime('%Y-%m-%d')

            if current_date_entry == previous_date_entry:
                times_measured_daily += 1
                sum_daily_temp += float(temperatures[i])
            else:
                # Append the average temperature for the day
                avg_temp_daily.append(round(sum_daily_temp / times_measured_daily, 2))
                date_temp.append(previous_date_entry)
                # Reset daily measurements
                sum_daily_temp = float(temperatures[i])
                times_measured_daily = 1

        # Append the last day's average
        avg_temp_daily.append(round(sum_daily_temp / times_measured_daily, 2))
        date_temp.append(current_date_entry)

        last_fetched_date = current_date  # Update last fetched date

        return jsonify({'timestamp': date_temp,'temperature': avg_temp_daily,})

# Route to save the current temperature into the database
@app.route('/save', methods=['POST'])
def save_temperature():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO temperatures (temperature, timestamp) VALUES (?, ?)", (latest_weather['temperature'], latest_weather['timestamp']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Temperature saved!'})

# Route to get the 5 most recent temperatures from the database
@app.route('/recent', methods=['GET'])
def get_recent_temperatures():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute("SELECT temperature, timestamp FROM temperatures ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{'temperature': row[0], 'timestamp': row[1]} for row in rows])

# Initialize database and start scheduler when the app runs
if __name__ == '__main__':
    init_db()  # Initialize the database
    start_scheduler()  # Start the background weather updater
    fetch_weather()  # Fetch initial weather data
    app.run(debug=True)

