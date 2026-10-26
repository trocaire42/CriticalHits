import reflex as rx
import asyncio
import logging
from typing import Any, Iterable
from sqlmodel import select, delete, tuple_
from sqlalchemy.orm import selectinload
from app.models import Game, ArenaChoice, User, Collection
from app.services.rank_matrix import RankMatrix
from app.util import ROUTES
from app.state.auth_state import AuthState

logger = logging.getLogger(__name__)

class DesyncError(ValueError): pass

class UIStatus:
    TOO_FEW  = "TOO_FEW"
    READY    = "READY"
    WINNER   = "WINNER"
    LOADING  = "LOADING"
    COMPLETE = "COMPLETE"
    ERROR    = "ERROR"

class ArenaState(rx.State):
    is_loading: bool = False
    modal_active: bool = False
    progress: int = 0
    choice_count: int = 0

    choice_made: bool = False
    current_pair: tuple[Game, Game] | None = None
    prev_pair: tuple[Game, Game] | None = None
    winner_index: int = -1

    ranked_results: list[dict[str, Any]] = []
    prev_ranks: dict[int, int] = {}

    _rank_matrix: RankMatrix | None = None
    _user_id: int = 0

    @rx.var
    def ui_state(self) -> str:
        if self.choice_made and self.winner_index in (0, 1):
            return UIStatus.WINNER
        
        if self.is_loading:
            return UIStatus.LOADING

        if self._rank_matrix is None:
            return UIStatus.ERROR

        if self._rank_matrix.node_count < 5:
            return UIStatus.TOO_FEW

        if self.progress == 100:
            return UIStatus.COMPLETE
        
        if self.current_pair is not None and len(self.current_pair) == 2:
            return UIStatus.READY

        return UIStatus.ERROR

    async def on_mount(self):
        """
        Called on page load/refresh. Checks user authentication and
        initializes state variables from database via _initialize_arena().
        """
        self.is_loading = True
        yield

        auth = await self.get_state(AuthState)
        self._user_id = auth.user_id
        
        if self._user_id:
            await self._initialize_arena()

        self.is_loading = False

    async def choose_winner(self, index: int):
        """
        Called when the user makes a choice between a pair of games in the arena.
        Starts the winner animation then calls handle_selection to update state variables and DB.

        Args:
            index: Index of the winning game in the current pair (0 = left, 1 = right)
        """
        if index not in (0, 1) or self.choice_made: return

        # Checks to ensure the user is logged in
        if not self._user_id:
            rx.redirect(f"{ROUTES['login']}?r={ROUTES['battle']}")
            return

        self.choice_made = True
        self.is_loading = True

        # Storing the previous pair in (winner, loser) order
        self.prev_pair = (self.current_pair[index], self.current_pair[1 - index])
        self.winner_index = index
        yield

        # Start updating database and calculating next pair
        update_task = asyncio.create_task(
            self._handle_selection(
                self.prev_pair[0].id,
                self.prev_pair[1].id
            )
        )

        # Wait for animations to play
        await asyncio.sleep(1.0)

        self.choice_made = False
        self.winner_index = -1
        yield

        # If background tasks aren't finished yet, wait for them
        try:
            await update_task
        except DesyncError:
            yield rx.toast.error("Data validation error. Resynchronizing application.")
            await self._initialize_arena()
        finally:
            self.is_loading = False

    async def undo_last_choice(self):
        """
        Reverts the user's most recent Arena choice via RankMatrix.undo(),
        then deletes the choice from the database and resynchronizes the UI.
        """
        if self.is_loading or self.choice_made: return
        self.is_loading = True
        yield

        # Checks to ensure the user is logged in
        if not self._user_id:
            rx.redirect(f"{ROUTES['login']}?r={ROUTES['battle']}")
            return

        # Undo the choice in the matrix and rebuild
        last_choice = self._rank_matrix.undo()

        if last_choice:
            try:
                async with rx.asession() as session:
                    # Delete the choice from the database
                    query = (
                        delete(ArenaChoice)
                        .where(
                            ArenaChoice.user_id == self._user_id,
                            ArenaChoice.winner_id == last_choice[0],
                            ArenaChoice.loser_id == last_choice[1]
                        )
                    )

                    await session.exec(query)
                    await session.commit()

                if self._rank_matrix.choices:
                    prev = await self._fetch_game_data(self._rank_matrix.choices[-1])
                    self.prev_pair = tuple(prev)
                else:
                    self.prev_pair = None

                yield rx.toast.success("Last Choice Reverted")
            except KeyError:
                # Matrix/database are out of sync, rebuild state
                yield rx.toast.error("Data validation error. Resynchronizing application.")
                await self._initialize_arena()
                return
            except Exception as e:
                logger.error(f"[!] Database error in undo: {e}")
                
                # Reinstate the choice to the matrix if the database delete fails
                self._rank_matrix.record(last_choice[0], last_choice[1])
            finally:
                self.choice_count = len(self._rank_matrix.choices)
                self.progress = self._rank_matrix.progress

                try:
                    await self._update_ranked_list()
                    await self._update_pair()
                except DesyncError:
                    yield rx.toast.error("Data validation error. Resynchronizing application.")
                    await self._initialize_arena()
                finally:
                    self.is_loading = False
        else:
            self.is_loading = False

    def open_modal(self):
        self.modal_active = True

    def close_modal(self):
        self.modal_active = False

    async def reset_all_choices(self):
        """
        Completely resets all user choices, deleting them from the database
        and refreshing to a 'blank slate' UI.
        """
        if self.is_loading: return
        self.is_loading = True
        yield

        # Checks to ensure the user is logged in
        if not self._user_id:
            rx.redirect(f"{ROUTES['login']}?r={ROUTES['battle']}")
            return

        try:
            async with rx.asession() as session:
                query = (
                    delete(ArenaChoice)
                    .where(ArenaChoice.user_id == self._user_id)
                )

                await session.exec(query)
                await session.commit()
        except Exception as e:
            yield rx.toast.error("Database error. Please try again.")
            logger.error(f"[!] Database error in reset: {e}")
        finally:
            await self._initialize_arena()
            yield rx.toast.success("All choices reset")
            self.is_loading = False

    async def _initialize_arena(self):
        """
        Refreshes state variables, (re)builds the matrix from the database,
        and calculates the next pair to display to the user.
        """
        # Resets state variables to prevent contamination by old data
        self._rank_matrix = None
        self.current_pair = None
        self.prev_pair = None
        self.choice_made = False
        self.winner_index = -1
        self.ranked_results = []
        self.prev_ranks = {}
        self.progress = 0
        self.choice_count = 0

        # Builds the graph from the DB and starts calculating the next pair
        await self._build_matrix()
        await self._update_pair()

    async def _build_matrix(self):
        """
        Rebuilds the matrix of arena results from scratch from the user's collection
        and recorded choices in the database. Automatically removes any orphaned or
        invalid choices from the database via RankMatrix's .skipped property.

        Only called from _initialize_arena(), which clears state variables first.
        """
        try:
            async with rx.asession() as session:
                # Gets a list of all games and choices associated with the user
                query = (
                    select(User)
                    .where(User.id == self._user_id)
                    .options(
                        selectinload(User.collection),
                        selectinload(User.choices)
                    )
                )
                result = await session.exec(query)
                user = result.one()

                game_ids = []
                choices = []
                for game in user.collection:
                    game_ids.append(game.id)
                for choice in user.choices:
                    choices.append((choice.winner_id, choice.loser_id))

                # Rebuilds the win/loss matrix from the user's prior choices
                self._rank_matrix = RankMatrix.from_choices(game_ids, choices)

                # If anything was skipped when building the matrix, they represent
                # invalid choices and should be removed from the database.
                skipped = self._rank_matrix.skipped
                if skipped:
                    logger.info(f"[*] Deleting {len(skipped)} invalid choices")
                    query = (
                        delete(ArenaChoice)
                        .where(
                            tuple_(ArenaChoice.winner_id, ArenaChoice.loser_id).in_(skipped)
                        )
                    )

                    await session.exec(query)
                    await session.commit()
        except Exception as e:
            logger.error(f"[!] Database error when building matrix: {e}")

        if self._rank_matrix:
            if self._rank_matrix.choices:
                try:
                    prev = await self._fetch_game_data(self._rank_matrix.choices[-1])
                    self.prev_pair = tuple(prev)
                except Exception as e:
                    logger.error(f"[!] Error fetching game data: {e}")

            self.choice_count = len(self._rank_matrix.choices)
            self.progress = self._rank_matrix.progress
            await self._update_ranked_list()

    async def _handle_selection(self, winner: int, loser: int):
        """
        Called when the user makes a choice between a pair of games in the arena.
        Updates the graph, current ranking, and next pair.

        Args:
            winner: integer ID for the winning game
            loser: integer ID for the losing game
        Raises:
            DesyncError: When an invalid or already-known selection is made.
        """
        success = False
        try:
            success = self._rank_matrix.record(winner, loser)
        except ValueError as e:
            logger.error(f"[!] Error recording ({winner}, {loser}): {e}")
            success = False

        # Re-initializing the state due to failure conditions
        if not success:
            raise DesyncError(f"Error recording ({winner}, {loser})")

        try:
            async with rx.asession() as session:
                choice = ArenaChoice(
                    user_id=self._user_id,
                    game_a_id=min(winner, loser),
                    game_b_id=max(winner, loser),
                    winner_id=winner,
                    loser_id=loser
                )
                session.add(choice)
                await session.commit()
        except Exception as e:
            logger.error(f"[!] Database error in choice handler: {e}")
            self._rank_matrix.undo()
        finally:
            self.choice_count = len(self._rank_matrix.choices)
            self.progress = self._rank_matrix.progress
            await self._update_ranked_list()
            await self._update_pair()

    async def _update_pair(self):
        """
        Gets the next pair of IDs from the RankMatrix and converts them to full Game objects for display.

        Raises:
            DesyncError: When an ID in the selected pair does not exist in the database
        """
        if not self._rank_matrix:
            self.current_pair = None
            return
        
        id_pair = self._rank_matrix.get_next_pair()
        if not id_pair:
            self.current_pair = None
            return

        # Retrieving Game objects from ids
        try:
            game_pair = await self._fetch_game_data(list(id_pair))
        except KeyError as e:
            raise DesyncError("Error retrieving next pair") from e
        except Exception as e:
            logger.error(f"[!] Error retrieving next pair: {e}")
            self.current_pair = None
            return

        self.current_pair = tuple(game_pair)

    async def _fetch_game_data(self, game_ids: Iterable[int]) -> list[Game]:
        """
        Converts a list of IDs to their corresponding full Game objects from the database.

        Args:
            game_ids: List of integer IDs to search
        Returns: 
            game_data: List of Game objects corresponding to the provided IDs (in order)
        Raises:
            KeyError: If an ID in the provided list does not exist in the database
        """
        if not game_ids:
            return []
        
        async with rx.asession() as session:
            query = (
                select(Game)
                .join(Collection)
                .where(
                    Game.id.in_(game_ids),
                    Collection.user_id == self._user_id
                )
            )
            result = await session.exec(query)
            games_map = {}
            for g in result.all():
                games_map[g.id] = g

        game_data = [games_map[gid] for gid in game_ids]
        return game_data

    async def _update_ranked_list(self):
        """
        Updates the arena leaderboard using tournament (1224) ranking system.
        Only accounts for games that have been in at least one arena pair.

        Raises:
            DesyncError: When an item ID in the matrix does not exist in the database
        """
        # Get scores (wins - losses + winrate) for all games with at least one comparison.
        scores = self._rank_matrix.get_scores()

        game_ids = list(scores.keys())
        game_ids.sort(key=lambda x: scores[x], reverse=True)

        try:
            games_list = await self._fetch_game_data(game_ids)
        except KeyError as e:
            raise DesyncError("Error updating ranked list") from e
        except Exception as e:
            logger.error(f"[!] Error updating leaderboard: {e}")
            return
        
        current_rank = 1
        ranked_output = []

        # Assign rank to each game in the retrieved list
        for i, entry in enumerate(games_list):
            if i > 0 and scores[game_ids[i]] < scores[game_ids[i-1]]:
                current_rank = i + 1

            prev_rank = self.prev_ranks.get(entry.id)
            change = ""

            if prev_rank:
                if current_rank > prev_rank:
                    change = "down"
                elif current_rank < prev_rank:
                    change = "up"
            else:
                change = "new"

            self.prev_ranks[entry.id] = current_rank
            ranked_output.append({"rank": current_rank, "game": entry, "change": change})

        self.ranked_results = ranked_output