import httpx
import os
import datetime
import asyncio
import reflex as rx
from logging import Logger
from weakref import WeakValueDictionary
from typing import Optional, Callable, Awaitable
from app.util import IMG_DIR, DEFAULT_IMAGE, IMG_SIZES
from app.models import Game

logger = Logger(__name__)

class IGDBManager:
    _access_token: Optional[str] = None
    _token_expiry: float = 0.0
    _token_lock = asyncio.Lock() # Prevents multiple users from requesting a token at once
    _download_semaphore = asyncio.Semaphore(10) # Limits concurrent image downloads
    _download_locks: WeakValueDictionary[int, asyncio.Lock] = WeakValueDictionary() # Prevents multiple downloads for a single image

    @classmethod
    async def igdb_auth(cls) -> str:
        """
        Retrieves an access token from Twitch for IGDB authorization.
        If one already exists, check if it is still valid.

        return: IGDB access token for use in API queries
        """
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

            logger.info("[*] Token expired or missing. Requesting new token from Twitch...")
            
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

    @staticmethod
    def get_image_url(cover_id: str, size: str) -> str:
        """
        Builds a URL string for an IGDB image.

        Args:
            cover_id: String representing the hash of the image to retrieve
            size: IGDB image size string (from IMG_SIZES)

        Return:
            URL to the requested image or DEFAULT_IMAGE if inputs are invalid
        """
        if not cover_id or size not in IMG_SIZES.values():
            return DEFAULT_IMAGE
        return f"https://images.igdb.com/igdb/image/upload/t_{size}/{cover_id}.jpg"

    @staticmethod
    def ui_get_image_url(cover_id: rx.Var, size: str) -> rx.Var:
        """
        Builds a URL string for an IGDB image. Accepts and returns Reflex Vars, for use in UI components.

        Args:
            cover_id: String representing the hash of the image to retrieve
            size: IGDB image size string (from IMG_SIZES)

        Return:
            URL to the requested image or DEFAULT_IMAGE if inputs are invalid
        """
        valid_size = size in IMG_SIZES.values()
        url = f"https://images.igdb.com/igdb/image/upload/t_{size}/{cover_id}.jpg"
        return rx.cond((cover_id) & (valid_size), url, DEFAULT_IMAGE)

    @classmethod
    async def cache_images(cls, games: list[Game], callback: Callable[[int], Awaitable[None]]):
        """
        Background task for caching images from IGDB.

        games: List of Game objects to check for cached images.
        callback: Callback function to report individual games' image status to the UI.
        """
        async with httpx.AsyncClient() as client:
            tasks = [cls._download_image(g, client, callback) for g in games]
            if tasks:
                await asyncio.gather(*tasks)

    @classmethod
    async def _download_image(cls, game: Game, client: httpx.AsyncClient, callback: Callable[[int], Awaitable[None]]):
        """
        Background task for downloading a single game's cover image from IGDB.
        Runs callback function once complete to report back to the UI.

        Args:
            game: Game object to check for cached image.
            client: http client to use for downloading images.
            callback: Callback function to report this game's image status to the UI.
        """
        game_id = game.id
        cover_id = game.igdb_cover_id

        if not game_id:
            return

        if not cover_id:
            await callback(game_id)
            return

        local_path = IMG_DIR / f"{cover_id}.jpg"

        # Checks if the file exists before requesting a lock
        if local_path.exists():
            await callback(game_id)
            return

        async with cls._download_locks.setdefault(game_id, asyncio.Lock()):
            remote_url = cls.get_image_url(cover_id, IMG_SIZES["lg_cover"])

            # Verifying the file wasn't created since the lock was requested and the remote URL is valid
            if local_path.exists() or remote_url == DEFAULT_IMAGE:
                await callback(game_id)
                return

            async with cls._download_semaphore:
                try:
                    res = await client.get(remote_url)
                    if res.status_code == 200:
                        await asyncio.to_thread(cls._write_file, local_path, res.content)
                        await callback(game_id)
                except Exception as e:
                    logger.error(f"Failed to sync {game_id}: {e}")

    @classmethod
    def _write_file(cls, path, content):
        with open(path, 'wb') as f:
            f.write(content)