import httpx
import os
import datetime
import asyncio
import reflex as rx
from typing import Optional, List, Any, Callable, Awaitable
from app.util import IMG_DIR

class IGDBManager:
    _access_token: Optional[str] = None
    _token_expiry: float = 0.0
    _token_lock = asyncio.Lock() # Prevents multiple users from requesting a token at once
    _download_semaphore = asyncio.Semaphore(10) # Limits concurrent image downloads
    _download_locks: dict[int, asyncio.Lock] = {} # Prevents multiple downloads for a single image

    @classmethod
    async def igdb_auth(cls) -> str:
        client_id = os.getenv("IGDB_CLIENT", "")
        client_secret = os.getenv("IGDB_SECRET", "")
        current_time = datetime.datetime.now().timestamp()

        # Check if we already have a valid token
        if cls._access_token and cls._token_expiry > (current_time + 60):
            return cls._access_token

        # If not, acquire lock to ensure only one request goes to Twitch
        async with cls._token_lock:
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

    @classmethod
    async def cache_images(cls, games: List[dict[str, Any]], callback: Callable[[int], Awaitable[None]]):
        async with httpx.AsyncClient() as client:
            tasks = [cls._download_image(g, client, callback) for g in games]
            if tasks:
                await asyncio.gather(*tasks)

    @classmethod
    async def _download_image(cls, game: dict[str, Any], client: httpx.AsyncClient, callback: Callable[[int], Awaitable[None]]):
        game_id = game.get("id")
        cover_id = game.get("igdb_cover_id")

        if not game_id:
            return

        local_path = IMG_DIR / f"{game_id}.jpg"

        if not cover_id or local_path.exists():
            await callback(game_id)
            return

        async with cls._download_locks.setdefault(game_id, asyncio.Lock()):
            # Verifying the file wasn't created since the lock was requested
            if local_path.exists():
                await callback(game_id)
                return

            remote_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover_id}.jpg"

            async with cls._download_semaphore:
                try:
                    res = await client.get(remote_url)
                    if res.status_code == 200:
                        await asyncio.to_thread(cls._write_file, local_path, res.content)
                        await callback(game_id)
                except Exception as e:
                    print(f"Failed to sync {game_id}: {e}")
                finally:
                    cls._download_locks.pop(game_id)

    @classmethod
    def _write_file(cls, path, content):
        with open(path, 'wb') as f:
            f.write(content)