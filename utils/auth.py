# utils/auth.py

from fastapi import Request, HTTPException

def extract_bearer_token(request: Request) -> str:
    """
    Extracts the Bearer token from the Authorization header.
    Raises HTTPException(401) if not present or invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    return auth_header.split("Bearer ")[1].strip()
