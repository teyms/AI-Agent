from datetime import datetime
from zoneinfo import ZoneInfo
import random
def get_weather(location: str):
    fake_weather_data = {
        "singapore": "30°C, rainy",
        "tokyo": "18°C, cloudy",
        "london": "10°C, windy"
    }

    return fake_weather_data.get(
        location.lower(),
        "Weather data not found."
    )


def calculator(expression: str):
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"
    
    
def get_current_time(city: str):
    try:
        timezones = {
            "singapore": "Asia/Singapore",
            "new york": "America/New_York",
            "london": "Europe/London",
            "tokyo": "Asia/Tokyo",
        }

        tz = ZoneInfo(timezones[city.lower()])
        current_time = datetime.now(tz)
        return current_time
    except Exception as e:
        return f"get current time error: {str(e)}"
    
def tell_joke(category="general"):
    jokes = {
        "general": [
            "Why don’t scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
        ],
        "programming": [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why was the JavaScript developer sad? Because he didn’t Node how to Express himself.",
        ],
        "dad": [
            "I only know 25 letters of the alphabet. I don’t know y.",
            "What do you call fake spaghetti? An impasta!",
        ]
    }

    category = category.lower()

    if category not in jokes:
        return f"Sorry, no jokes found for category '{category}'."

    return random.choice(jokes[category])    
    
    