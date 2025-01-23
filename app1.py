import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from io import BytesIO

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

        .stSlider .st-bc .stSlider-rail {
            background-color: #333;
        }

        .stSlider .st-bc .stSlider-handle {
            background-color: #ff4b2b;
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

        .stText {
            font-size: 22px;
            font-weight: bold;
            color: #e0e0e0;
            text-align: center;
        }

        .stMarkdown {
            color: #e0e0e0;
            font-size: 18px;
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

        .stMarkdown {
            color: #ecf0f1;
        }

        .stSelectbox, .stRadio {
            background-color: #34495e;
            color: #ecf0f1;
            border: none;
            font-size: 16px;
        }

        .stSelectbox .st-ae, .stRadio .st-ae {
            color: #34495e;
        }
    </style>
""", unsafe_allow_html=True)

# API Key and Base URL
API_KEY = st.secrets["general"]["API_KEY"]
CITY_DB_PATH = CITY_DB_PATH = 'city_database.csv'  # Path to city database

# Load the city database
try:
    city_df = pd.read_csv(CITY_DB_PATH)
except Exception as e:
    st.error(f"Error loading city database: {e}")
    exit()

# Function to fetch city coordinates
def get_city_coordinates(city_name):
    try:
        city_info = city_df[city_df['City'].str.lower() == city_name.lower()]
        if city_info.empty:
            st.error(f"City '{city_name}' not found in the database.")
            return None, None
        lat = city_info['Lat'].values[0]
        lon = city_info['Long'].values[0]
        return lat, lon
    except Exception as e:
        st.error(f"Error fetching city coordinates: {e}")
        return None, None

# Function to fetch weather data from OpenWeather API
def fetch_weather_data(lat, lon, forecast_type="3-hour"):
    try:
        if forecast_type == "daily":
            url = "https://api.openweathermap.org/data/2.5/forecast/daily"  # 7-day daily forecast (deprecated for free plans)
        else:
            url = "https://api.openweathermap.org/data/2.5/forecast"  # 3-hour forecast for 5 days
        
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric",  # Use metric units (Celsius)
            "appid": API_KEY
        }
        
        # Fetch data from OpenWeather API
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract weather data
        forecast_list = data["list"]
        forecast_data = []
        for forecast in forecast_list:
            forecast_data.append({
                "datetime": forecast["dt_txt"] if "dt_txt" in forecast else forecast["dt"],
                "temperature": forecast["main"]["temp"],
                "humidity": forecast["main"]["humidity"],
                "pressure": forecast["main"]["pressure"],
                "weather": forecast["weather"][0]["description"]
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(forecast_data)
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
    except KeyError as e:
        st.error(f"Unexpected data structure: {e}")
    return None

# Streamlit UI
def main():
    st.title("Weather Forecast Application for India 🇮🇳")
    
    # Display city name input first
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
        lat, lon = get_city_coordinates(city_name)
        if lat is not None and lon is not None:
            st.write(f"Fetching weather data for {city_name} (Lat: {lat}, Lon: {lon})...")
            
            # Fetch weather data (3-hour forecast by default)
            weather_data = fetch_weather_data(lat, lon, forecast_type="3-hour")
            
            if weather_data is not None and not weather_data.empty:
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
                    # Plotting temperature trends with Plotly
                    fig_temp = go.Figure()
                    fig_temp.add_trace(go.Scatter(x=weather_data["datetime"], y=weather_data["temperature"],
                                                  mode='lines+markers', name='Temperature (°C)', line=dict(color='orange'),
                                                  hovertemplate="Temperature: %{y}°C<br>Date: %{x}<extra></extra>"))
                    fig_temp.update_layout(
                        title=f"Temperature Trend for {city_name}",
                        xaxis_title="Datetime",
                        yaxis_title="Temperature (°C)",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_temp)

                if show_humidity:
                    # Plotting humidity trends with Plotly
                    fig_humidity = go.Figure()
                    fig_humidity.add_trace(go.Scatter(x=weather_data["datetime"], y=weather_data["humidity"],
                                                      mode='lines+markers', name='Humidity (%)', line=dict(color='blue'),
                                                      hovertemplate="Humidity: %{y}%<br>Date: %{x}<extra></extra>"))
                    fig_humidity.update_layout(
                        title=f"Humidity Trend for {city_name}",
                        xaxis_title="Datetime",
                        yaxis_title="Humidity (%)",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_humidity)

                if show_pressure:
                    # Plotting pressure trends with Plotly
                    fig_pressure = go.Figure()
                    fig_pressure.add_trace(go.Scatter(x=weather_data["datetime"], y=weather_data["pressure"],
                                                      mode='lines+markers', name='Pressure (hPa)', line=dict(color='green'),
                                                      hovertemplate="Pressure: %{y} hPa<br>Date: %{x}<extra></extra>"))
                    fig_pressure.update_layout(
                        title=f"Pressure Trend for {city_name}",
                        xaxis_title="Datetime",
                        yaxis_title="Pressure (hPa)",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig_pressure)

                # Display map if selected
                if show_map:
                    # Display weather map with weather conditions
                    weather_map = folium.Map(location=[lat, lon], zoom_start=12)
                    folium.Marker([lat, lon], popup=f"{city_name} Weather", icon=folium.Icon(icon="cloud")).add_to(weather_map)

                    # Render map in Streamlit using folium_static
                    st.write("### Weather Map")
                    folium_static(weather_map)

                # Add a "Made with ❤️ by Pranab"
                st.markdown("<br><hr><br><h5 style='text-align: center;'>Made with ❤️ by Pranab</h5>", unsafe_allow_html=True)

            else:
                st.error(f"No weather data available for {city_name}.")
        else:
            st.error(f"Invalid city name: {city_name}. Please enter a valid city name.")
    else:
        st.info("Please enter a city name and click 'Search' to fetch weather data.")

if __name__ == "__main__":
    main()
