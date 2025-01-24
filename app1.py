import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta

# Custom CSS for dark mode and UI enhancements
st.markdown("""
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background-color: #1e1e1e;
            color: #e0e0e0;
        }

        .stButton button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 12px 24px;
            font-size: 18px;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .stButton button:hover {
            background-color: #45a049;
            transform: translateY(-3px);
        }

        .stSlider .st-bc {
            background: linear-gradient(to right, #ff416c, #ff4b2b);
        }

        .stTextInput input {
            border-radius: 15px;
            padding: 12px;
            font-size: 18px;
            border: 2px solid #ccc;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }

        .stTextInput input:focus {
            border-color: #ff4b2b;
            box-shadow: 0px 0px 10px rgba(255, 75, 43, 0.5);
        }

        .box {
            background-color: #2c3e50;
            padding: 15px;
            border-radius: 15px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            margin-bottom: 10px;
            color: #ecf0f1;
        }

        .box h4 {
            color: #ff4b2b;
            font-size: 22px;
        }

        .box p {
            font-size: 16px;
            color: #ecf0f1;
        }
    </style>
""", unsafe_allow_html=True)

# API Key and Base URL
API_KEY = st.secrets["general"]["API_KEY"]

# Function to fetch weather data from OpenWeatherMap API
def fetch_weather_data(city_name, forecast_type="3-hour"):
    try:
        # Fetch city data including latitude and longitude
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct"
        geocoding_params = {"q": city_name, "limit": 1, "appid": API_KEY}
        geo_response = requests.get(geocoding_url, params=geocoding_params)
        geo_response.raise_for_status()
        city_data = geo_response.json()

        if not city_data:
            st.error(f"City '{city_name}' not found. Please try again.")
            return None, None, None

        lat, lon = city_data[0]["lat"], city_data[0]["lon"]

        # Fetch weather forecast data
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"  # 3-hour forecast for 5 days
        forecast_params = {"lat": lat, "lon": lon, "units": "metric", "appid": API_KEY}
        forecast_response = requests.get(forecast_url, params=forecast_params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Extract weather data
        forecast_list = forecast_data["list"]
        forecast_df = pd.DataFrame([
            {
                "datetime": forecast["dt_txt"],
                "temperature": forecast["main"]["temp"],
                "humidity": forecast["main"]["humidity"],
                "pressure": forecast["main"]["pressure"],
                "weather": forecast["weather"][0]["description"]
            }
            for forecast in forecast_list
        ])
        return lat, lon, forecast_df

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None, None, None

# Function to fetch current weather data
def fetch_current_weather(lat, lon):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "units": "metric", "appid": API_KEY}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching current weather data: {e}")
        return None

# Function to convert UNIX timestamp to local time
def convert_to_local_time(unix_time, timezone_offset):
    utc_time = datetime.utcfromtimestamp(unix_time)
    local_time = utc_time + timedelta(seconds=timezone_offset)
    return local_time.strftime('%I:%M %p')

# Streamlit UI
def main():
    st.title("Weather Forecast Application 🌐 🇮🇳")

    # City name input
    city_name = st.text_input("Enter the city name:", "").strip()

    # Slider for number of predictions
    num_predictions = st.slider("Select the number of predictions to display:", 1, 40, 10)

    # Output options directly before the search
    st.write("### Select Outputs")
    show_map = st.checkbox("Show Map", value=True)
    show_humidity = st.checkbox("Show Humidity", value=True)
    show_pressure = st.checkbox("Show Pressure", value=True)
    show_temperature = st.checkbox("Show Temperature", value=True)

    # Search button behavior
    search_button = st.button("Search")

    if search_button and city_name:
        st.write(f"Fetching weather data for {city_name}...")
        lat, lon, weather_data = fetch_weather_data(city_name)

        if lat and lon and weather_data is not None:
            # Fetch and display current weather
            current_weather = fetch_current_weather(lat, lon)
            if current_weather:
                temp = current_weather["main"]["temp"]
                feels_like = current_weather["main"]["feels_like"]
                desc = current_weather["weather"][0]["description"].capitalize()
                icon = current_weather["weather"][0]["icon"]
                humidity = current_weather["main"]["humidity"]
                pressure = current_weather["main"]["pressure"]
                wind_speed = current_weather["wind"]["speed"]
                visibility = current_weather["visibility"] / 1000
                sunrise = convert_to_local_time(current_weather["sys"]["sunrise"], current_weather["timezone"])
                sunset = convert_to_local_time(current_weather["sys"]["sunset"], current_weather["timezone"])

                st.markdown(f"""
                    <div class="box">
                        <h4>Current Weather in {city_name}</h4>
                        <p><img src="http://openweathermap.org/img/wn/{icon}@2x.png" style="float:right; margin-right:50px; border-radius: 10px; width: 150px; height: 150px" alt="Weather icon">
                        {desc}<br>
                        <strong>Temperature:</strong> {temp}°C (Feels like {feels_like}°C)<br>
                        <strong>Humidity:</strong> {humidity}%<br>
                        <strong>Pressure:</strong> {pressure} hPa<br>
                        <strong>Wind:</strong> {wind_speed} m/s<br>
                        <strong>Visibility:</strong> {visibility} km<br>
                        <strong>Sunrise:</strong> {sunrise}<br>
                        <strong>Sunset:</strong> {sunset}</p>
                        <div style="clear:both;"></div>
                    </div>
                    """, unsafe_allow_html=True)

            st.write(f"### Weather Overview for {city_name}:")
            st.markdown(f"#### Weather condition and predictions for the next {num_predictions} periods:")

            # Display weather data for selected number of predictions
            for i in range(num_predictions):
                weather_desc = weather_data["weather"][i]
                temp = weather_data["temperature"][i]
                humidity = weather_data["humidity"][i]
                pressure = weather_data["pressure"][i]
                time = weather_data["datetime"][i]

                weather_icon = "☀️" if "clear" in weather_desc else "☁️" if "cloud" in weather_desc else "🌧️"

                # Display the weather details in a box
                st.markdown(f"""
                <div class="box">
                    <h4>{i+1}. Time: {time}</h4>
                    <p><span style="font-size: 20px; color: #0073e6;">{weather_icon} {weather_desc}</span><br>
                    Temp: {temp}°C | Humidity: {humidity}% | Pressure: {pressure} hPa</p>
                </div>
                """, unsafe_allow_html=True)

            # Display graphs based on user selections
            if show_temperature:
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(x=weather_data["datetime"], y=weather_data["temperature"],
                                              mode='lines+markers', name='Temperature (°C)', line=dict(color='orange')))
                fig_temp.update_layout(title="Temperature Trend", xaxis_title="Datetime", yaxis_title="Temperature (°C)", template="plotly_dark")
                st.plotly_chart(fig_temp)

            if show_humidity:
                fig_humidity = go.Figure()
                fig_humidity.add_trace(go.Scatter(x=weather_data["datetime"], y=weather_data["humidity"],
                                                  mode='lines+markers', name='Humidity (%)', line=dict(color='blue')))
                fig_humidity.update_layout(title="Humidity Trend", xaxis_title="Datetime", yaxis_title="Humidity (%)", template="plotly_dark")
                st.plotly_chart(fig_humidity)

            if show_pressure:
                fig_pressure = go.Figure()
                fig_pressure.add_trace(go.Scatter(x=weather_data["datetime"], y=weather_data["pressure"],
                                                  mode='lines+markers', name='Pressure (hPa)', line=dict(color='green')))
                fig_pressure.update_layout(title="Pressure Trend", xaxis_title="Datetime", yaxis_title="Pressure (hPa)", template="plotly_dark")
                st.plotly_chart(fig_pressure)

            # Display map if selected
            if show_map:
                weather_map = folium.Map(location=[lat, lon], zoom_start=12)
                folium.Marker([lat, lon], popup=f"{city_name} Weather", icon=folium.Icon(icon="cloud")).add_to(weather_map)
                st.write("### Weather Map")
                folium_static(weather_map)

            # Footer
            st.markdown("<br><hr><br><h5 style='text-align: center;'>Made with ❤️ by Pranab</h5>", unsafe_allow_html=True)

        else:
            st.error(f"No weather data available for {city_name}.")
    else:
        st.info("Please enter a city name and click 'Search' to fetch weather data.")

if __name__ == "__main__":
    main()
