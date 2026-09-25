import reflex as rx
import httpx
import os
import datetime
from sqlmodel import select
from typing import List, Dict, Any
from app.services.igdb_service import igdb_manager
from app.models import Game
from app.util import *

class BuilderState(rx.State):
    search_query: str = ""
    search_results: List[Dict[str, Any]] = []
    active_search: str = "" # Stores most recent search query for pagination
    search_offset: int = 0 # Search offset for pagination
    search_page_size: int = 50 # Page size for search pagination
    search_more: bool = False
    search_key: int = 0
    igdb_client: str = os.getenv("IGDB_CLIENT", "") # API Client ID
    added_games: List[Dict[str, Any]] = []
    is_loading: bool = False

    def set_search_query(self, value: str):
        self.search_query = value.strip().lower()

    async def on_mount(self):
        self.is_loading = True
        yield
        print("[!] Page mount triggered")
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
                        "igdb_id": r.igdb_id,
                        "title": r.title,
                        "img": f"{r.id}.jpg" if r.igdb_cover_id else None
                    })

                    if r.igdb_cover_id:
                        # Download image if it wasn't already cached
                        local_path = IMG_DIR / f"{r.id}.jpg"
                        remote_path = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{r.igdb_cover_id}.jpg"
                        if not local_path.exists():
                            try:
                                async with httpx.AsyncClient() as client:
                                    img_response = await client.get(remote_path)
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

    ### Search handling

    # Start a new search
    async def search_new(self):
        if len(self.search_query) < 3:
            return

        self.is_loading = True
        yield

        self.search_offset = 0
        self.search_results = []
        self.search_key += 1
        self.active_search = self.search_query

        try:
            await self._search_games()
        except Exception as e:
            rx.toast.error(f"Search failed: {e}")
        finally:
            self.is_loading = False

    # Continue a previous search (next page)
    async def search_continue(self):
        if not self.active_search:
            return
        
        self.is_loading = True
        yield

        self.search_offset += self.search_page_size

        try:
            await self._search_games()
        except Exception as e:
            rx.toast.error(f"Search failed: {e}")
        finally:
            self.is_loading = False

    # Search logic (called via one of the above methods)
    async def _search_games(self):
        token = await igdb_manager.igdb_auth()
        headers = {
            "Client-ID": self.igdb_client,
            "Authorization": f"Bearer {token}"
        }

        query = (
            'fields name, cover.image_id, involved_companies.company.name, involved_companies.developer,'
            ' first_release_date, platforms.name, platforms.platform_logo.url;\n'
            f'search "{self.active_search}";\n'
            f'limit {self.search_page_size};\n'
            f'offset {self.search_offset};\n'
            'where game_type != (3, 11, 14) & version_parent = null;' # Exclude bundles, ports, updates, and alternate versions
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.igdb.com/v4/games",
                headers=headers,
                content=query
            )

            if response.status_code == 200:
                data = response.json()

                if not data:
                    self.search_more = False
                    return

                for r in data:
                    igdb_id = r.get("id")
                    title = r.get("name", "")
                    image_id = r.get("cover", {}).get("image_id", "")
                    year = ""

                    platforms = []
                    platform_logos = []
                    developers = []

                    if r.get("platforms"):
                        for p in r["platforms"]:
                            platforms.append(p.get("name", ""))
                            if p.get("platform_logo"):
                                platform_logos.append(p["platform_logo"].get("url", ""))

                    if r.get("involved_companies"):
                        for c in r["involved_companies"]:
                            # If this company has 'developer: true' add it to the list
                            if c.get("developer", False):
                                developers.append(c.get("company", {}).get("name", ""))

                    release = r.get("first_release_date")
                    if release:
                        try:
                            year = str(datetime.datetime.fromtimestamp(release).year)
                        except (ValueError, OSError, OverflowError):
                            year = "N/A"
                    else:
                        year = "N/A"

                    self.search_results.append({
                        "id": None,
                        "igdb_id": igdb_id,
                        "title": title,
                        "year": year,
                        "platforms": ", ".join(platforms) if platforms else "N/A",
                        "platform_logos": platform_logos,
                        "developers": ", ".join(developers) if developers else "N/A",
                        "cover_id": image_id
                    })

                # If we got a full page, assume there might be more
                self.search_more = len(data) == self.search_page_size
            else:
                print(f"IGDB API Error: {response.status_code} - {response.text}")
                rx.toast.error("An API error occurred.")

        self._refresh_search_status()


    def _refresh_search_status(self):
        for r in self.search_results:
            r["id"] = next((g["id"] for g in self.added_games if g["igdb_id"] == r["igdb_id"]), None)


    ### Games list management (add/remove)
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
                igdb_id=game_data["igdb_id"],
                igdb_cover_id=game_data["cover_id"],
                title=game_data["title"],
                release_year=int(game_data["year"]) if game_data["year"] != "N/A" else 0,
                platform=game_data["platforms"],
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