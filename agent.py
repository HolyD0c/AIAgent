from openai import OpenAI
import dateparser
import json
import requests

# === AI Client (Gemini) ===
client = OpenAI(
    api_key="INSERT API KEY HERE",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# === Extract weather forecast from Open-Meteo ===
def get_weather_forecast(latitude, longitude, date, hour):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&hourly=temperature_2m,weathercode"
        f"&timezone=Europe/Berlin"
    )

    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Failed to get weather data:", response.text)
        return

    data = response.json()
    times = data["hourly"]["time"]
    temps = data["hourly"]["temperature_2m"]
    codes = data["hourly"]["weathercode"]

    # Find matching hour
    target_time = f"{date}T{hour:02d}:00"
    if target_time in times:
        idx = times.index(target_time)
        temperature = temps[idx]
        weathercode = codes[idx]
        description = get_weather_description(weathercode)

        print(f"\n🌤️ Weather forecast for {date} at {hour:02d}:00")
        print(f"📍 Temperature: {temperature}°C")
        print(f"🌡️ Condition: {description}")
    else:
        print(f"⚠️ No forecast data found for {target_time}")

def get_weather_description(code):
    code_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return code_map.get(code, "Unknown")

# === Ask user ===
user_input = input("Ask about the weather (e.g., 'Weather in Paris tomorrow at 3 PM'): ")

# === Ask Gemini to extract structured info ===
completion = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[
        {
            "role": "system",
            "content": (
                "Extract the weather query from user input and return JSON with keys: "
                "`location` (city or place), `date` (as text), and `time` (for single time) or `time_range` (object with `start` and `end` times in 24h format or natural language like '3 PM')."
            )
        },
        {"role": "user", "content": user_input},
    ],
)

# === Extract Gemini output ===
output_text = completion.choices[0].message.content.strip()
if output_text.startswith("```json"):
    output_text = output_text.split("```json")[1].split("```")[0].strip()

weather_query = json.loads(output_text)

# === Parse date + hour ===
parsed_date = dateparser.parse(weather_query["date"], settings={"PREFER_DATES_FROM": "future"})
if not parsed_date:
    print("⚠️ Could not parse date.")
    exit()

iso_date = parsed_date.date().isoformat()
hours = []

if "time_range" in weather_query:
    start_time = dateparser.parse(weather_query["time_range"]["start"])
    end_time = dateparser.parse(weather_query["time_range"]["end"])

    if not start_time or not end_time:
        print("⚠️ Could not parse time range.")
        exit()

    start_hour = start_time.hour
    end_hour = end_time.hour

    if end_hour < start_hour:
        print("⚠️ Invalid time range (end before start).")
        exit()

    hours = list(range(start_hour, end_hour + 1))
else:
    parsed_time = dateparser.parse(weather_query["time"])
    if not parsed_time:
        print("⚠️ Could not parse time.")
        exit()
    hours = [parsed_time.hour]

# === Convert city to lat/lon (basic) ===
location = weather_query["location"]
geocode_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
geo_response = requests.get(geocode_url, headers={"User-Agent": "WeatherBot/1.0"})

if geo_response.status_code == 200 and geo_response.json():
    geo_data = geo_response.json()[0]
    lat = float(geo_data["lat"])
    lon = float(geo_data["lon"])
    print(f"\n📍 Location: {location} ({lat}, {lon})")
    if len(hours) == 1:
        print(f"📅 Date: {iso_date}, 🕒 Time: {hours[0]}:00")
    else:
        print(f"📅 Date: {iso_date}, ⏱️ Time Range: {hours[0]}:00 to {hours[-1]}:00")
    for hour in hours:
        get_weather_forecast(lat, lon, iso_date, hour)
else:
    print(f"❌ Failed to find location: {location}")
