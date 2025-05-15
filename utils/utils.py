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
    url = f"{DIARY_URL}?date={date}"
    headers = {"Authorization": f"Bearer {token}"}

    print(f"[fetch_diary_by_date] GET {url} with headers={headers}")
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # 404: NotFoundException 에 대응하여 빈 리스트로
        if resp.status_code == 404:
            print(f"[fetch_diary_by_date] 404 received → returning []")
            return []
        # 그 외 에러는 그대로 올리기
        raise

    data = resp.json()
    texts: List[str] = []

    # 1) JSON Array of objects
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "text" in item:
                texts.append(str(item["text"]))

    # 2) JSON Object with entries / entry
    elif isinstance(data, dict):
        # entries: [ {text:...}, … ]
        if isinstance(data.get("entries"), list):
            for item in data["entries"]:
                if isinstance(item, dict) and "text" in item:
                    texts.append(str(item["text"]))

        # entry: single object or list
        elif "entry" in data:
            ent = data["entry"]
            if isinstance(ent, dict) and "text" in ent:
                texts.append(str(ent["text"]))
            elif isinstance(ent, list):
                for sub in ent:
                    if isinstance(sub, dict) and "text" in sub:
                        texts.append(str(sub["text"]))

    # 3) 기타(사전형) → 문자열값만
    else:
        for v in data.values():
            if isinstance(v, str):
                texts.append(v)

    return texts
