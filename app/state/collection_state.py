import reflex as rx
import httpx
import os
import datetime
from sqlmodel import select
from typing import List, Any
from app.services.igdb_service import IGDBManager
from app.models import Game
from app.util import *

class CollectionState(rx.State):
    search_query: str = ""
    search_results: List[dict[str, Any]] = []
    active_search: str = "" # Stores most recent search query for pagination
    search_offset: int = 0 # Search offset for pagination
    search_page_size: int = 50 # Page size for search pagination
    search_more: bool = False
    search_key: int = 0
    igdb_client: str = os.getenv("IGDB_CLIENT", "") # API Client ID
    added_games: List[dict[str, Any]] = []
    game_ids: dict[int, int] = {} # Matches IGDB IDs to database IDs for easy lookup
    is_loading: bool = False
    synced_ids: set[int] = set()

    def set_search_query(self, value: str):
        self.search_query = value.strip().lower()

    async def on_mount(self):
        """
        Initial page load, collects UI information via _list_load,
        starts caching/verifying cover images via background task.
        """
        self.is_loading = True
        yield
        await self._list_load()
        yield type(self).cache_covers
        self.is_loading = False

    # Loading games list from database
    async def _list_load(self):
        """
        Re-synchronizes the UI from the database, ensuring that
        the displayed data matches the source of truth.
        Starts a background process to download any missing cover images
        """
        self.added_games = []
        self.game_ids = {}
        self.synced_ids = set()

        try:
            async with rx.asession() as session:
                result = await session.exec(select(Game))

                for r in result.all():
                    self.added_games.append({
                        "id": r.id,
                        "igdb_id": r.igdb_id,
                        "igdb_cover_id": r.igdb_cover_id,
                        "title": r.title,
                        "img": f"{r.id}.jpg" if r.igdb_cover_id else None
                    })

                    self.game_ids[r.igdb_id] = r.id
        except Exception as e:
            print(f"Database error: {e}")

        if self.added_games:
            self._sort_games()

    @rx.event(background=True)
    async def cache_covers(self):
        """
        Background helper function to download cover images without
        blocking UI.
        """
        async with self:
            games = list(self.added_games)

        await IGDBManager.cache_images(games, self._img_confirm)

    async def _img_confirm(self, game_id: int):
        """
        Callback function for cover image caching background task.
        When an image finishes downloading (or is confirmed to exist),
        add the game's id to synced_ids so the UI knows it's safe to display the image.

        game_id: int ID corresponding to models.Game.id
        """
        async with self:
            self.synced_ids.add(game_id)

    def _sort_games(self):
        """
        Alphabetically sorts the added_games list for the sidebar
        """
        # Helper function to omit leading articles (the/an/a)
        def natural_sort_key(game: dict):
            title = game["title"].lower()
            for article in ["the ", "an ", "a "]:
                if title.startswith(article):
                    title = title[len(article):]
            return title

        self.added_games = sorted(self.added_games, key=natural_sort_key)

    ### Search handling
    async def search_new(self):
        """
        Starts a new IGDB search. Empties search_results and sets
        search_offset to 0 to start from scratch
        """
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

    async def search_continue(self):
        """
        Retrieves the next page of results from the previous search
        Increments search_offset by search_page_size
        """
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

    async def _search_games(self):
        """
        Sends the search query to IGDB API handler
        Number of entries to retrieve determined by search_page_size
        """
        token = await IGDBManager.igdb_auth()
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
            # Exclude bundles, ports, updates, alternate versions, and games without a release date
            'where game_type != (3, 11, 14) & version_parent = null & first_release_date != null;'
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
        """
        Determines whether each item in the search results already exists in the DB
        in order to properly display add/remove buttons in the UI
        """
        for r in self.search_results:
            r["id"] = self.game_ids.get(r.get("igdb_id", 0))

    ### Games list management (add/remove)
    async def toggle_game(self, game_data: dict):
        """
        Determines whether the given game exists in the database,
        calls the appropriate function (add/remove), then re-syncs
        the UI from the source of truth (DB).

        game_data: dict representing a single game
        """
        self.is_loading = True
        yield

        try:
            if game_data.get("id"):
                # Exists in DB; delete it
                await self._delete_game(game_data["id"])
            else:
                # Does not exist in DB; add it
                await self._add_game(game_data)
        except Exception as e:
            print(f"Database error: {e}")
            rx.toast.error("Database error. Please try again.")
        finally:
            await self._list_load()
            yield type(self).cache_covers()
            self._refresh_search_status()
            self.is_loading = False

    async def _add_game(self, game_data: dict):
        """
        Adds a game to the database

        game_data: dict representing a single game
        """
        async with rx.asession() as session:
            new_game = Game(
                igdb_id=game_data["igdb_id"],
                igdb_cover_id=game_data["cover_id"],
                title=game_data["title"],
                release_year=int(game_data["year"]) if game_data["year"] != "N/A" else None,
                platform=game_data["platforms"],
            )
            session.add(new_game)
            await session.commit()

    async def _delete_game(self, game_id: int):
        """
        Removes a game from the database

        game_id: int ID corresponding to models.Game.id
        """
        async with rx.asession() as session:
            result = await session.exec(select(Game).where(Game.id == game_id))
            to_delete = result.first()
            if to_delete:
                await session.delete(to_delete)
                await session.commit()