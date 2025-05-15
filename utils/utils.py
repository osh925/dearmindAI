import requests
import datetime
from typing import List, Mapping, Optional

HISTORY_URL = "https://dearmind-be.onrender.com/chat/history"
DIARY_URL   = "https://dearmind-be.onrender.com/diary/by-date"

def fetch_chat_history(token: str) -> List[Mapping[str, str]]:
    """
    Returns a list of dicts like {"role":"user"|"assistant","content": "..."}
    """
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[fetch_chat_history] GET {HISTORY_URL} with headers={headers}")
    resp = requests.get(HISTORY_URL, headers=headers, timeout=5)
    resp.raise_for_status()
    return resp.json()

def fetch_diary_by_date(token: str, date: Optional[str] = None) -> List[str]:
    """
    Returns the diary entries for the given date (ISO YYYY-MM-DD).
    If no `date` is provided, uses today’s date.
    """
    date = date or datetime.date.today().isoformat()
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[fetch_diary_by_date] GET {DIARY_URL}?date={date} with headers={headers}")
    resp = requests.get(f"{DIARY_URL}?date={date}", headers=headers, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    # normalize into a list of strings
    if isinstance(data, dict):
        if "entries" in data and isinstance(data["entries"], list):
            return data["entries"]
        if "entry" in data:
            return [data["entry"]]
        # fallback: return any string fields
        return [v for v in data.values() if isinstance(v, str)]
    elif isinstance(data, list):
        return [str(item) for item in data]
    else:
        return []
