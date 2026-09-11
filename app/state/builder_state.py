import reflex as rx
import httpx
import os
from sqlmodel import select, func
from typing import List, Dict, Any
from app.models import Game
from app.util import *

class BuilderState(rx.State):
    search_query: str = ""
    search_exact: bool = False
    search_results: List[Dict[str, Any]] = []
    search_next: str = ""
    search_more: bool = False
    added_games: List[Dict[str, Any]] = []
    is_loading: bool = False
    api_key: str = os.getenv("RAWG_API_KEY", "")

    async def on_mount(self):
        self.is_loading = True
        yield
        await self.list_load()
        self.is_loading = False

    def set_search_query(self, value: str):
        self.search_query = value.strip().lower()

    def toggle_search_mode(self):
        self.search_exact = not self.search_exact

    @staticmethod
    def _natural_sort_key(game: dict):
        title = game["title"].lower()
        for article in ["the ", "an ", "a "]:
            if title.startswith(article):
                title = title[len(article):]
        return title

    async def list_load(self):
        self.added_games = []
        unsort = []

        try:
            async with rx.asession() as session:
                result = await session.exec(select(Game).order_by(func.lower(Game.title)))

                for r in result.all():
                    unsort.append({
                        "id": r.id,
                        "title": r.title,
                        "img": f"{r.id}.png"
                    })

                    # Download and Cache Image if it doesn't exist
                    local_path = IMG_DIR / f"{r.id}.png"
                    if not local_path.exists():
                        try:
                            async with httpx.AsyncClient() as client:
                                img_response = await client.get(r.cover_url)
                                if img_response.status_code == 200:
                                    with open(local_path, 'wb') as f:
                                        f.write(img_response.content)
                        except Exception as e:
                            print(f"Image download failed for {local_path}: {e}")
        except Exception as e:
            print(f"Database error: {e}")

        self.added_games = sorted(unsort, key=BuilderState._natural_sort_key)

    async def search_new(self):
        if len(self.search_query) < 3 or not self.api_key:
            return
        
        search_type = "&search_exact=true" if self.search_exact else ""
        api_url = f"https://api.rawg.io/api/games?key={self.api_key}&search={self.search_query}{search_type}"
        self.search_results = []
        return self._search_games(api_url)

    async def search_continue(self):
        if not self.search_next or not self.api_key:
            return
        
        return self._search_games(self.search_next)

    async def _search_games(self, api_url: str):
        self.is_loading = True
        yield

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url)
                if response.status_code == 200:
                    data = response.json()

                    # Determining whether additional pages exist in the search
                    if data["next"]:
                        self.search_next = data["next"]
                        self.search_more = True
                    else:
                        self.search_next = ""
                        self.search_more = False

                    for r in data["results"]:
                        self.search_results.append({
                            "id": r["id"],
                            "title": r["name"],
                            "year": r["released"].split("-")[0] if r.get("released") else "N/A",
                            "platform": ", ".join([p["platform"]["name"] for p in (r.get("platforms") or [])[:2]]),
                            "cover": r["background_image"],
                            "active": True if any(g["id"] == r["id"] for g in self.added_games) else False
                        })
                else:
                    rx.toast.error(f"API Error: {response.status_code}. Please check your connection.")
            except Exception as e:
                print(f"Search error: {e}")
                rx.toast.error(f"An unexpected error occurred during search.")
            finally:
                self.is_loading = False

    async def add_game(self, game_data: dict):
        self.is_loading = True
        yield

        game_id = game_data["id"]

        try:
            async with rx.asession() as session:
                new_game = Game(
                    id=game_id,
                    title=game_data["title"],
                    release_year=int(game_data["year"]) if game_data["year"] != "N/A" else 0,
                    platform=game_data["platform"],
                    cover_url=game_data["cover"]
                )
                session.add(new_game)
                await session.commit()
        except Exception as e:
            print(f"Database error: {e}")

        # Refresh sidebar
        await self.list_load()
        self.refresh_search_status()
        self.is_loading = False

    async def delete_game(self, game_id: int):
        self.is_loading = True
        yield

        try:
            async with rx.asession() as session:
                result = await session.exec(select(Game).where(Game.id == game_id))
                if result:
                    await session.delete(result.first())
                    await session.commit()
        except Exception as e:
            print(f"Database delete error: {e}")

        # Refresh sidebar
        await self.list_load()
        self.refresh_search_status()
        self.is_loading = False

    async def toggle_game(self, game_data: dict):
        game_id = game_data["id"]
        if any(g["id"] == game_id for g in self.added_games):
            return self.delete_game(game_id)
        else:
            return self.add_game(game_data)

    def refresh_search_status(self):
        if not self.search_results or not self.added_games:
            return

        for r in self.search_results:
            if any(g["id"] == r["id"] for g in self.added_games):
                r["active"] = True
            else:
                r["active"] = False