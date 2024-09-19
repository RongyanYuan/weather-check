"use client";
import { useEffect, useState } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement);

const Home = () => {
  const [weather, setWeather] = useState<any>({});
  const [recentReadings, setRecentReadings] = useState<any[]>([]);
  const [isUpdating, setIsUpdating] = useState(true);
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  const [weatherHistory, setWeatherHistory] = useState<{ temperature: string[], timestamp: number[] } | null>(null);

  // Function to fetch current weather data from the Flask backend
  const fetchWeather = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:5000/weather');
      setWeather(res.data);
    } catch (err) {
      console.error('Error fetching weather:', err);
    }
  };

  // Function to fetch recent temperature readings from the Flask backend
  const fetchRecentReadings = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:5000/recent');
      setRecentReadings(res.data);
    } catch (err) {
      console.error('Error fetching recent readings:', err);
    }
  };

  // Function to save current temperature reading
  const saveTemperature = async () => {
    try {
      await axios.post('http://127.0.0.1:5000/save', {
        temperature: weather.temperature,
        timestamp: weather.timestamp,
      });
    } catch (err) {
      console.error('Error saving temperature:', err);
    }
  };

  // Fetch weather history from Flask backend
  const fetchWeatherHistory = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:5000/history');
      setWeatherHistory(res.data);
    } catch (err) {
      console.error('Error fetching weather history:', err);
    }
  };

  // useEffect to handle auto-refresh every 60 seconds
  useEffect(() => {
    // Fetch data on initial load
    fetchWeather();
    fetchWeatherHistory();

    // Set up interval for auto-refresh if updating is enabled
    if (isUpdating) {
      const interval = setInterval(() => {
        fetchWeather();
        fetchWeatherHistory();
      }, 60000); // 60 seconds interval
      setTimer(interval);
    }

    // Cleanup the interval on component unmount or when updating is disabled
    return () => {
      if (timer) {
        clearInterval(timer);
      }
    };
  }, [isUpdating]);

  // Toggle updating on or off
  const toggleUpdating = () => {
    setIsUpdating(!isUpdating);
    if (!isUpdating && timer) {
      clearInterval(timer); // Stop auto-refresh if paused
    }
  };

  return (
    <div>
      <h1>New York Weather</h1>
      <p>Current Temperature: {weather.temperature ? `${weather.temperature}°C` : 'N/A'}</p>
      <p>Timestamp: {weather.timestamp || 'N/A'}</p>
      
      {/* Button to toggle auto-refresh */}
      <button onClick={toggleUpdating}>
        {isUpdating ? 'Pause' : 'Play'}
      </button>

      {/* Button to save the current temperature */}
      <button onClick={saveTemperature}>
        Save Current Temperature
      </button>

      {/* Separate button to fetch recent readings */}
      <button onClick={fetchRecentReadings}>
        Obtain Recent Readings
      </button>

      <h2>Recent Temperature Readings</h2>
      {/* Display the 5 most recent temperature readings */}
      {recentReadings.length > 0 ? (
        recentReadings.map((reading, index) => (
          <p key={index}>
            {reading.temperature}°C at {reading.timestamp}
          </p>
        ))
      ) : (
        <p>No recent readings available.</p>
      )}

      <h2>Average Temperature History (Last 5 Days)</h2>
      {/* Line chart to display temperature history */}
      {weatherHistory ? (
        <Line
          data={{
            labels: weatherHistory.timestamp, // Dates
            datasets: [
              {
                label: 'Average Temperature (°C)',
                data: weatherHistory.temperature, // Average temperatures
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
              },
            ],
          }}
        />
      ) : (
        <p>Loading temperature history...</p>
      )}
    </div>
  );
};

export default Home;
