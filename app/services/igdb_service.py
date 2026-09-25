import httpx
import os
import datetime
import asyncio
from typing import Optional

class IGDBManager:
    _access_token: Optional[str] = None
    _token_expiry: float = 0.0
    _lock = asyncio.Lock() # Prevents multiple users from requesting a token at once

    @classmethod
    async def igdb_auth(cls) -> str:
        client_id = os.getenv("IGDB_CLIENT", "")
        client_secret = os.getenv("IGDB_SECRET", "")
        current_time = datetime.datetime.now().timestamp()

        # Check if we already have a valid token
        if cls._access_token and cls._token_expiry > (current_time + 60):
            return cls._access_token

        # If not, acquire lock to ensure only one request goes to Twitch
        async with cls._lock:
            # Check if the token was already refreshed since requesting the lock
            if cls._access_token and cls._token_expiry > (current_time + 60):
                return cls._access_token

            print("[*] Token expired or missing. Requesting new token from Twitch...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://id.twitch.tv/oauth2/token",
                    params={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "client_credentials"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    cls._access_token = data.get("access_token")
                    cls._token_expiry = current_time + data.get("expires_in", 3600)
                    return cls._access_token
                else:
                    raise Exception(f"IGDB Auth Failed: {response.text}")

# Create a singleton instance (though we use the class methods)
igdb_manager = IGDBManager()