import reflex as rx
import httpx
import os
from sqlmodel import select
from typing import List, Dict, Any
from app.models import Game
from app.util import *

class BuilderState(rx.State):
    search_query: str = ""
    search_exact: bool = False
    search_results: List[Dict[str, Any]] = []
    search_next: str = ""
    search_more: bool = False
    search_key: int = 0
    added_games: List[Dict[str, Any]] = []
    is_loading: bool = False
    api_key: str = os.getenv("RAWG_API_KEY", "")

    def set_search_query(self, value: str):
        self.search_query = value.strip().lower()

    def toggle_search_mode(self):
        self.search_exact = not self.search_exact

    async def on_mount(self):
        self.is_loading = True
        yield
        await self._list_load()
        self.is_loading = False

    # Loading games list from database
    async def _list_load(self):
        self.added_games = []
        unsort = []

        try:
            async with rx.asession() as session:
                result = await session.exec(select(Game))

                for r in result.all():
                    unsort.append({
                        "id": r.id,
                        "rawg_id": r.rawg_id,
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

    @staticmethod
    def _natural_sort_key(game: dict):
        title = game["title"].lower()
        for article in ["the ", "an ", "a "]:
            if title.startswith(article):
                title = title[len(article):]
        return title

    # Search handling
    async def search_new(self):
        if len(self.search_query) < 3 or not self.api_key:
            return

        self.is_loading = True
        yield
        
        search_type = "&search_exact=true" if self.search_exact else ""
        api_url = f"https://api.rawg.io/api/games?key={self.api_key}&page_size=50&search={self.search_query}{search_type}"
        self.search_results = []
        self.search_key += 1
        await self._search_games(api_url)

        self.is_loading = False

    async def search_continue(self):
        if not self.search_next or not self.api_key:
            return
        
        self.is_loading = True
        yield

        await self._search_games(self.search_next)

        self.is_loading = False

    async def _search_games(self, api_url: str):
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
                        # TODO: Handle null background_image
                        self.search_results.append({
                            "id": None,
                            "rawg_id": r["id"],
                            "title": r["name"],
                            "year": r["released"].split("-")[0] if r.get("released") else "N/A",
                            "platform": ", ".join([p["platform"]["name"] for p in (r.get("platforms") or [])[:2]]),
                            "cover": r["background_image"],
                        })
                else:
                    rx.toast.error(f"API Error: {response.status_code}. Please check your connection.")
            except Exception as e:
                print(f"Search error: {e}")
                rx.toast.error(f"An unexpected error occurred during search.")
            finally:
                self._refresh_search_status()

    def _refresh_search_status(self):
        for r in self.search_results:
            r["id"] = next((g["id"] for g in self.added_games if g["rawg_id"] == r["rawg_id"]), None)


    # Games list management (add/remove)
    async def toggle_game(self, game_data: dict):
        self.is_loading = True
        yield

        try:
            if game_data.get("id"):
                await self._delete_game(game_data["id"])
            else:
                await self._add_game(game_data)
        except Exception as e:
            print(f"Database error: {e}")
            rx.toast.error("Database error. Please try again.")
        finally:
            await self._list_load()
            self._refresh_search_status()
            self.is_loading = False

    async def _add_game(self, game_data: dict):
        async with rx.asession() as session:
            new_game = Game(
                rawg_id=game_data["rawg_id"],
                title=game_data["title"],
                release_year=int(game_data["year"]) if game_data["year"] != "N/A" else 0,
                platform=game_data["platform"],
                cover_url=game_data["cover"],
            )
            session.add(new_game)
            await session.commit()

    async def _delete_game(self, game_id: int):
        async with rx.asession() as session:
            result = await session.exec(select(Game).where(Game.id == game_id))
            to_delete = result.first()
            if to_delete:
                await session.delete(to_delete)
                await session.commit()