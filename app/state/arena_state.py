import reflex as rx
import networkx as nx
import random
from typing import List, Dict, Any
from sqlmodel import select
from app.models import Game, ArenaChoice

class ArenaState(rx.State):
    is_loading: bool = False
    completion: int = 0
    current_pair: List[Dict[str, Any]] = []
    ranked_results: List[Dict[str, Any]] = []
    _graph: nx.DiGraph = nx.DiGraph()

    # Initial page load
    async def on_mount(self):
        self.is_loading = True
        yield

        await self._initialize_arena()
        self.is_loading = False

    # Refreshes state variables, builds graph from DB, calculates next pair
    async def _initialize_arena(self):
        # Resets state variables to prevent contamination by old data
        self._graph = nx.DiGraph()
        self.current_pair = []
        self.ranked_results = []
        self.completion = 0

        # Builds the graph from the DB and starts calculating the next pair
        await self._build_graph()
        await self._get_next_pair()

    # Rebuilds the graph from scratch based on DB
    async def _build_graph(self):
        try:
            # Collects win/loss results from DB
            async with rx.asession() as session:
                # Gets a list of all games to compare and adds nodes to the graph
                result = await session.exec(select(Game))
                all_games = result.all()
                game_ids = [g.id for g in all_games]
                new_graph = nx.DiGraph()
                new_graph.add_nodes_from(game_ids)

                # Gets wins/losses
                result = await session.exec(select(ArenaChoice))
                choices = result.all()

                # Creates graph edges for each win (winner->loser)
                for c in choices:
                    new_graph.add_edge(c.winner_id, c.loser_id)

                # Calculates 'implied' wins and stores the resulting graph
                self._graph = nx.transitive_closure(new_graph)
        except Exception as e:
            print(f"Database error: {e}")

        self._update_progress()
        await self._update_ranked_list()

    # Updates graph, ranking, and next pair after the user chooses a winner
    async def handle_selection(self, winner: int, loser: int):
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
                choice = ArenaChoice(winner_id=winner, loser_id=loser)
                session.add(choice)
                await session.commit()

            self._incremental_closure(winner, loser)
        except Exception as e:
            print(f"[!] Database error: {e}")

        self._update_progress()
        await self._update_ranked_list()
        await self._get_next_pair()
        self.is_loading = False

    # Instead of running transitive_closure on the entire graph,
    # only check nodes directly implicated by the new edge (u->v)
    def _incremental_closure(self, u: int, v: int):
        predecessors = list(self._graph.predecessors(u)) + [u]
        successors = list(self._graph.successors(v)) + [v]

        for x in predecessors:
            for y in successors:
                if x != y: # Preventing self-loops
                    self._graph.add_edge(x, y)


    # Proof-of-concept: find a random untested pair
    async def _get_next_pair(self):
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
                        print(f"[!] Error: {e}")
                        self.current_pair = []
                    
                    return

        self.current_pair = [] # Ranking complete

    # Retrieves id, title, release year, and image from DB for each game ID in a list
    # Raises a KeyError if an item in the list does not exist in the DB
    async def _fetch_game_data(self, game_ids: List[int]):
        if not game_ids:
            return []
        
        async with rx.asession() as session:
            sql = select(Game).where(Game.id.in_(game_ids))
            res = await session.exec(sql)
            games_map = {}
            for g in res.all():
                games_map[g.id] = {
                    "id": g.id,
                    "title": g.title,
                    "year": g.release_year,
                    "img": f"{g.id}.jpg" if g.igdb_cover_id else None
                }

        game_data = [games_map[gid] for gid in game_ids]
        return game_data

    # Updates ranks for all games using tournament (1224) ranking system.
    async def _update_ranked_list(self):
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
            ranked_output = await self._fetch_game_data([s["id"] for s in scores])
        except KeyError:
            rx.toast.error("Data validation error. Resynchronizing state.")
            await self._initialize_arena()
            return
        except Exception as e:
            print(f"[!] Error: {e}")
            return
        
        current_rank = 1

        # Assign rank to each game in the retrieved list
        for i, entry in enumerate(ranked_output):
            if i > 0 and scores[i]["score"] < scores[i-1]["score"]:
                current_rank = i + 1

            entry["rank"] = current_rank

        self.ranked_results = ranked_output

    # Calculates completion percentage to display a progress bar
    def _update_progress(self):
        n = self._graph.number_of_nodes()
        if n < 2:
            self.completion = 0
            return

        max_edges = (n * (n - 1)) / 2
        current_edges = self._graph.number_of_edges()
        self.completion = int((current_edges / max_edges) * 100)