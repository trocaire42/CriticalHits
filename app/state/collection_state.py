import reflex as rx
import httpx
import os
import datetime
from logging import Logger
from sqlmodel import select, delete, or_
from sqlalchemy.orm import selectinload
from app.services.igdb_service import IGDBManager
from app.state.auth_state import AuthState
from app.models import User, Game, Collection, ArenaChoice
from app.util import ROUTES

logger = Logger(__name__)

class CollectionState(rx.State):
    search_query: str = ""
    search_results: list[Game] = []
    active_search: str = "" # Stores most recent search query for pagination
    search_offset: int = 0 # Search offset for pagination
    search_page_size: int = 50 # Page size for search pagination
    search_more: bool = False
    search_key: int = 0
    igdb_client: str = os.getenv("IGDB_CLIENT", "") # API Client ID
    added_games: list[Game] = []
    game_ids: dict[int, int] = {} # Matches IGDB IDs to database IDs for easy lookup
    is_loading: bool = False
    synced_ids: set[int] = set()

    def set_search_query(self, value: str):
        self.search_query = value.strip().lower()

    async def on_mount(self):
        """
        Initial page load. Confirms a user is logged in,
        collects UI information via _list_load, and
        starts caching/verifying cover images via background task.
        """
        self.is_loading = True
        yield

        await self._list_load()
        yield type(self).cache_covers

        self.is_loading = False

    async def _list_load(self):
        """
        Re-synchronizes the UI from the database, ensuring that
        the displayed data matches the source of truth.
        Starts a background process to download any missing cover images
        """
        self.added_games = []
        self.game_ids = {}
        self.synced_ids = set()

        auth = await self.get_state(AuthState)
        user_id = auth.current_user_id

        try:
            async with rx.asession() as session:
                # Pulls all games in the user's collection from the database
                query = (
                    select(User)
                    .where(User.id == user_id)
                    .options(selectinload(User.collection))
                )
                result = await session.exec(query)
                user = result.one()

                for g in user.collection:
                    self.added_games.append(g)
                    self.game_ids[g.igdb_id] = g.id
        except Exception as e:
            logger.error(f"[!] Database error: {e}")

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

        game_id: Integer ID for the updated game
        """
        async with self:
            self.synced_ids.add(game_id)

    def _sort_games(self):
        """
        Alphabetically sorts the added_games list for the sidebar
        """
        # Helper function to omit leading articles (the/an/a)
        def natural_sort_key(game: Game):
            title = game.title.lower()
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
            ' first_release_date, platforms.name;\n'
            f'search "{self.active_search}";\n'
            f'limit {self.search_page_size};\n'
            f'offset {self.search_offset};\n'
            # Exclude dlc, bundles, ports, addons, updates, alternate versions, and games without a release date
            'where game_type != (1, 3, 11, 13, 14) & version_parent = null & first_release_date != null;'
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

                    year = None
                    platforms = []
                    developers = []

                    if r.get("platforms"):
                        for p in r['platforms']:
                            platforms.append(p.get("name", ""))

                    if r.get("involved_companies"):
                        for c in r['involved_companies']:
                            # If this company has 'developer: true' add it to the list
                            if c.get("developer", False):
                                developers.append(c.get("company", {}).get("name", ""))

                    release = r.get("first_release_date")
                    if release:
                        try:
                            year = datetime.datetime.fromtimestamp(release).year
                        except (ValueError, OSError, OverflowError):
                            year = None
                    else:
                        year = None

                    self.search_results.append(Game(
                        igdb_id=igdb_id,
                        igdb_cover_id=image_id,
                        title=title,
                        release_year=year,
                        platforms=", ".join(platforms) if platforms else None,
                        developers=", ".join(developers) if developers else None,
                    ))

                # If we got a full page, assume there might be more
                self.search_more = len(data) == self.search_page_size
            else:
                logger.error(f"IGDB API Error: {response.status_code} - {response.text}")
                rx.toast.error("An API error occurred.")

        self._refresh_search_status()

    def _refresh_search_status(self):
        """
        Determines whether each item in the search results already exists in the DB
        in order to properly display add/remove buttons in the UI
        """
        for r in self.search_results:
            r.id = self.game_ids.get(r.igdb_id)

    ### Games list management (add/remove)
    async def toggle_game(self, game: Game):
        """
        Determines whether the given game exists in the database,
        calls the appropriate function (add/remove), then re-syncs
        the UI from the source of truth (DB).

        game_data: dict representing a single game
        """
        self.is_loading = True
        yield

        try:
            if game.id:
                # Exists in DB; delete it
                await self._delete_game(game.id)
            else:
                # Does not exist in DB; add it
                await self._add_game(game)
        except Exception as e:
            logger.error(f"[!] Database error: {e}")
            rx.toast.error("Database error. Please try again.")
        finally:
            await self._list_load()
            yield type(self).cache_covers()
            self._refresh_search_status()
            self.is_loading = False

    async def _add_game(self, new_game: Game):
        """
        Adds a game to the database if it doesn't already exist,
        then adds it to the user's collection.

        new_game: models.Game object to be added
        """
        auth = await self.get_state(AuthState)
        user_id = auth.current_user_id
        if user_id == 0:
            return rx.redirect(ROUTES['login'])

        async with rx.asession() as session:
            query = select(Game).where(Game.igdb_id == new_game.igdb_id)
            result = await session.exec(query)
            g = result.first()

            if not g:
                # Game doesn't exist in the database; create it.
                session.add(new_game)
                await session.flush()
                await session.refresh(new_game)
            else:
                new_game = g

            user_game = Collection(
                user_id=user_id,
                game_id=new_game.id
            )

            session.add(user_game)
            await session.commit()

    async def _delete_game(self, game_id: int):
        """
        Removes a game from the user's collection in the database

        game_id: Integer ID for the game to remove
        """
        auth = await self.get_state(AuthState)
        user_id = auth.current_user_id
        if user_id == 0:
            rx.redirect(ROUTES['login'])
            return

        async with rx.asession() as session:
            query = select(Collection).where(Collection.user_id == user_id, Collection.game_id == game_id)
            result = await session.exec(query)
            to_delete = result.first()
            if to_delete:
                # Removing the game from the user's collection
                await session.delete(to_delete)

                # Also removing the user's arena choices involving this game
                query = (
                    delete(ArenaChoice)
                    .where(
                        ArenaChoice.user_id == user_id,
                        or_(
                            ArenaChoice.winner_id == game_id,
                            ArenaChoice.loser_id == game_id
                        )
                    )
                )
                await session.exec(query)
                await session.commit()