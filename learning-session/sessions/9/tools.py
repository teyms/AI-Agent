from datetime import datetime
import logging

try:
    from logging_config import logger
except ImportError:
    logger = logging.getLogger(__name__)

try:
    from sqlite_vec_store import (
        init_db,
        search_similar
    )
    conn = init_db()
except ImportError:
    conn = None

    def search_similar(conn, query):
        return [
            (
                "Company policy says annual leave must be requested before taking leave.",
                "company_policy.txt"
            ),
            (
                "RAG agents retrieve relevant knowledge before creating an answer.",
                "agent_notes.txt"
            )
        ]


def get_current_time():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def get_weather(location):
    fake_weather_data = {
        "singapore": "30C, rainy",
        "tokyo": "18C, cloudy",
        "london": "10C, windy",
        "new york": "-3C, snowing",
    }

    return fake_weather_data.get(
        location.lower(),
        "Weather data not found."
    )


def calculator(expression):

    try:
        return str(eval(expression))

    except Exception as e:
        return f"Calculation error: {str(e)}"


SUSPICIOUS_PHRASES = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard previous instructions",
    "system prompt",
    "developer message",
    "reveal your instructions",
    "you are now",
]


def detect_prompt_injection(text):
    text_lower = text.lower()

    for phrase in SUSPICIOUS_PHRASES:
        if phrase in text_lower:
            return phrase

    return None


def search_knowledge_base(query):

    results = search_similar(
        conn,
        query
    )

    formatted = []

    for result in results:
        suspicious_phrase = detect_prompt_injection(result[0])
        if suspicious_phrase:
            logger.warning(
                f"Prompt injection detected in {result[1]}: {suspicious_phrase}"
            )
            continue

        formatted.append({
            "text": result[0],
            "source": result[1]
        })

    return formatted


# from datetime import datetime
# from zoneinfo import ZoneInfo


# def get_weather(location: str):
#     fake_weather_data = {
#         "singapore": "30°C, rainy",
#         "tokyo": "18°C, cloudy",
#         "london": "10°C, windy",
#         "new york": "-3°C, snowing",
#     }

#     return fake_weather_data.get(
#         location.lower(),
#         "Weather data not found."
#     )


# def calculator(expression: str):
#     try:
#         result = eval(expression)
#         return str(result)
#     except Exception as e:
#         return f"Calculation error: {str(e)}"


# def current_time(city: str):
#     timezones = {
#         "singapore": "Asia/Singapore",
#         "johor": "Asia/Kuala_Lumpur",
#         "kuala lumpur": "Asia/Kuala_Lumpur",
#         "tokyo": "Asia/Tokyo",
#         "london": "Europe/London",
#         "new york": "America/New_York",
#     }

#     timezone_name = timezones.get(city.lower())
#     if not timezone_name:
#         return f"Timezone not found for {city}."

#     now = datetime.now(ZoneInfo(timezone_name))
#     return now.strftime("%Y-%m-%d %H:%M:%S %Z")


# def currency_conversion(amount: float, from_currency: str, to_currency: str):
#     rates_to_usd = {
#         "usd": 1.0,
#         "myr": 0.21,
#         "sgd": 0.74,
#         "jpy": 0.0064,
#         "gbp": 1.27,
#     }

#     source = from_currency.lower()
#     target = to_currency.lower()

#     if source not in rates_to_usd or target not in rates_to_usd:
#         return "Currency not supported."

#     usd_amount = float(amount) * rates_to_usd[source]
#     converted_amount = usd_amount / rates_to_usd[target]
#     return f"{amount} {from_currency.upper()} is about {converted_amount:.2f} {to_currency.upper()}."


# def search_notes(query: str):
#     notes = [
#         "AI agents use an LLM to decide actions and call tools.",
#         "RAG means retrieval-augmented generation.",
#         "Memory lets an agent reuse useful context from earlier turns.",
#     ]

#     matches = [note for note in notes if query.lower() in note.lower()]
#     if not matches:
#         return "No matching notes found."

#     return "\n".join(matches)
