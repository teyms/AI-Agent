import json
from pathlib import Path


PROFILE_PATH = Path("user_profiles.json")

DEFAULT_PROFILE = {
    "preferred_language": "English",
    "city": "Singapore",
    "timezone": "Asia/Singapore"
}


def load_profiles():
    if not PROFILE_PATH.exists():
        return {}

    with PROFILE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_user_profile(thread_id):
    profiles = load_profiles()
    return profiles.get(
        thread_id,
        DEFAULT_PROFILE
    )


def save_user_profile(
    thread_id,
    preferred_language,
    city,
    timezone
):
    profiles = load_profiles()
    profiles[thread_id] = {
        "preferred_language": preferred_language,
        "city": city,
        "timezone": timezone
    }

    with PROFILE_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            profiles,
            f,
            indent=2
        )
