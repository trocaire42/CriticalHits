import reflex as rx
import networkx as nx
import random
from logging import Logger
from typing import Any
from enum import Enum
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.models import Game, ArenaChoice, User
from app.util import ROUTES
from app.state.auth_state import AuthState

logger = Logger(__name__)

class UIStatus:
    TOO_FEW  = "TOO_FEW"
    READY    = "READY"
    LOADING  = "LOADING"
    COMPLETE = "COMPLETE"
    ERROR    = "ERROR"

class ArenaState(rx.State):
    is_loading: bool = False
    completion: int = 0
    current_pair: list[Game] = []
    ranked_results: list[dict[str, Any]] = []
    _graph: nx.DiGraph = nx.DiGraph()

    @rx.var
    def ui_state(self) -> str:
        if self.completion == 100:
            return UIStatus.COMPLETE

        if len(self._graph.nodes()) < 5:
            return UIStatus.TOO_FEW

        if len(self.current_pair) == 2:
            return UIStatus.READY

        if self.is_loading:
            return UIStatus.LOADING

        return UIStatus.ERROR

    async def on_mount(self):
        """
        Called on page load/refresh. Checks for an active user, then
        initializes state variables from database via _initialize_arena().
        """
        self.is_loading = True
        yield
        await self._initialize_arena()
        self.is_loading = False

    async def _initialize_arena(self):
        """
        Refreshes state variables, (re)builds the graph from the database,
        and calculates the next pair to display to the user.
        """
        # Checks to ensure the user is logged in
        auth = await self.get_state(AuthState)
        user_id = auth.current_user_id

        if not user_id:
            return rx.redirect(f"{ROUTES['login']}?r={ROUTES['battle']}")
        
        # Resets state variables to prevent contamination by old data
        self._graph = nx.DiGraph()
        self.current_pair = []
        self.ranked_results = []
        self.completion = 0

        # Builds the graph from the DB and starts calculating the next pair
        await self._build_graph()
        await self._get_next_pair()

    async def _build_graph(self):
        """
        Rebuilds the graph of arena results from scratch.
        Creates graph edges for explicit wins given in the database,
        then uses transitive_closure to calculate implied wins.
        """
        try:
            async with rx.asession() as session:
                auth = await self.get_state(AuthState)
                user_id = auth.current_user_id
                # Gets a list of all games and choices associated with the user
                query = (
                    select(User)
                    .where(User.id == user_id)
                    .options(
                        selectinload(User.collection),
                        selectinload(User.choices)
                    )
                )
                result = await session.exec(query)
                user = result.one()

                # Builds the graph
                new_graph = nx.DiGraph()
                for game in user.collection:
                    new_graph.add_node(game.id)

                # Adds 'explicit' wins from the database
                for choice in user.choices:
                    new_graph.add_edge(choice.winner_id, choice.loser_id)

                # Calculates 'implied' wins and stores the resulting graph
                self._graph = nx.transitive_closure(new_graph)
        except Exception as e:
            logger.error(f"[!] Database error: {e}")

        self._update_progress()
        await self._update_ranked_list()

    async def handle_selection(self, winner: int, loser: int):
        """
        Called when the user makes a choice between a pair of games in the arena.
        Updates the graph, current ranking, and next pair.

        Args:
            winner: integer ID for the winning game
            loser: integer ID for the losing game
        """
        # Checks to ensure the user is logged in
        auth = await self.get_state(AuthState)
        user_id = auth.current_user_id

        if not user_id:
            rx.redirect(f"{ROUTES['login']}?r={ROUTES['battle']}")
            return
        
        self.is_loading = True
        yield

        # Preventing self-loops due to an inconsistent/stale graph state
        if nx.has_path(self._graph, loser, winner) or nx.has_path(self._graph, winner, loser):
            rx.toast.error("Data validation error. Resynchronizing state.")
            await self._initialize_arena()
            self.is_loading = False
            return

        try:
            async with rx.asession() as session:
                choice = ArenaChoice(
                    user_id=user_id,
                    game_a_id=min(winner, loser),
                    game_b_id=max(winner, loser),
                    winner_id=winner,
                    loser_id=loser
                )
                session.add(choice)
                await session.commit()

            self._incremental_closure(winner, loser)
        except Exception as e:
            logger.error(f"[!] Database error: {e}")
        finally:
            self._update_progress()
            await self._update_ranked_list()
            await self._get_next_pair()
            self.is_loading = False

    def _incremental_closure(self, u: int, v: int):
        """
        Alternative to transitive_closure that only checks nodes
        that are directly implicated by the new edge (u->v)

        Args:
            u: integer ID for the winning game
            v: integer ID for the losing game
        """
        predecessors = list(self._graph.predecessors(u)) + [u]
        successors = list(self._graph.successors(v)) + [v]

        for x in predecessors:
            for y in successors:
                if x != y: # Preventing self-loops
                    self._graph.add_edge(x, y)

    async def _get_next_pair(self):
        """
        Calculates the next pair of games to display to the user.
        Currently a proof-of-concept that returns a random pair without a known edge.
        """
        nodes = list(self._graph.nodes)
        random.shuffle(nodes)
        if len(nodes) < 2:
            return

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]

                if not self._graph.has_edge(u, v) and not self._graph.has_edge(v, u):
                    try:
                        self.current_pair = await self._fetch_game_data([u,v])
                    except KeyError:
                        rx.toast.error("Data validation error. Resynchronizing state.")
                        await self._initialize_arena()
                    except Exception as e:
                        logger.error(f"[!] Error: {e}")
                        self.current_pair = []
                    
                    return

        self.current_pair = [] # Ranking complete

    async def _fetch_game_data(self, game_ids: list[int]) -> list[Game]:
        """
        Converts a list of IDs to their corresponding full Game objects from the database.

        Args:
            game_ids: List of integer IDs to search

        Return: 
            List of Game objects corresponding to the provided IDs (in order)

        Raises:
            KeyError: If an ID in the provided list does not exist in the database
        """
        if not game_ids:
            return []
        
        async with rx.asession() as session:
            query = select(Game).where(Game.id.in_(game_ids))
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
        """
        if not self._graph.nodes:
            return

        scores = []
        for node in self._graph.nodes:
            wins = self._graph.out_degree(node)
            losses = self._graph.in_degree(node)

            # Only adding to win_counts if the game has been in at least one match
            if wins + losses > 0:
                # Reducing ties - we add win percentage to number of wins to act as a tiebreaker
                score = wins + (wins / (wins + losses))
                scores.append({"id": node, "score": score})

        scores.sort(key=lambda x: x["score"], reverse=True)

        try:
            games_list = await self._fetch_game_data([s["id"] for s in scores])
        except KeyError:
            rx.toast.error("Data validation error. Resynchronizing state.")
            await self._initialize_arena()
            return
        except Exception as e:
            logger.error(f"[!] Error: {e}")
            return
        
        current_rank = 1
        ranked_output = []

        # Assign rank to each game in the retrieved list
        for i, entry in enumerate(games_list):
            if i > 0 and scores[i]["score"] < scores[i-1]["score"]:
                current_rank = i + 1

            ranked_output.append({"rank": current_rank, "game": entry})

        self.ranked_results = ranked_output

    def _update_progress(self):
        """
        Calculates completion percentage (an integer 0-100) to display a progress bar in the arena.
        Accounts for all edges (explicit and implied) to show the user how close to 'done' they are.
        """
        n = self._graph.number_of_nodes()
        if n < 2:
            self.completion = 0
            return

        max_edges = (n * (n - 1)) // 2
        current_edges = self._graph.number_of_edges()
        self.completion = (current_edges * 100) // max_edges