import math
from typing import Optional
import numpy as np

class RankMatrix:
    def __init__(self, game_ids: list[int]):
        self._ids: list[int] = list(game_ids)
        self._index: dict[int, int] = {g: i for i, g in enumerate(self._ids)}
        n = len(self._ids)
        self._matrix = np.zeros((n, n), dtype=bool)
        self._log: list[tuple[int, int]] = []
        self.skipped: list[tuple[int, int]] = []  # choices ignored by from_choices

    @property
    def node_count(self) -> int:
        return len(self._ids)

    @property
    def items(self) -> list[int]:
        return list(self._ids)

    @property
    def choices(self) -> list[tuple[int, int]]:
        return list(self._log)

    @property
    def is_complete(self) -> bool:
        n = len(self._ids)
        return int(self._matrix.sum()) == (n * (n - 1)) // 2

    @property
    def progress(self) -> int:
        """
        Progress bar value, integer 0-100. Capped at 99 until the ranking is complete.
        """
        n = len(self._ids)
        choice_count = len(self._log)

        if n < 2 or choice_count == 0:
            return 0

        current_edges = self._matrix.sum()
        max_edges = (n * (n - 1) // 2)

        if current_edges == max_edges:
            return 100

        # Estimate for expected number of total decisions
        # Observed results: 79-94 at n=25; 213-242 at n=50; 532-590 at n=100; 1305-1400 at n=200
        # avg = log2(n!) * C where C ~ (1.04 .. 1.11)
        # Overestimate C slightly to 1.12 to account for high outliers and avoid hitting 99% too early.
        # This gives us 93.71 at n=25; 239.91 at n=50; 587.74 at n=100; 1394.825 at n=200. Slightly below max observed.
        # Using Stirling's approximation to avoid massive factorial ints
        target = 1.12 * ((n * math.log2(n)) - (n * math.log2(math.e)) + (0.5 * math.log2(2 * math.pi * n)))

        # 'uncertainty gap' representing the % of decisions remaining
        gap = (max_edges - current_edges) / max_edges

        # multiply target estimate and uncertainty gap for an estimate of remaining choices
        remaining = target * gap

        # Estimated completion (as float (0 .. 1))
        progress_pct = choice_count / (choice_count + remaining)

        # Converts to integer percentage, capped at 99 to prevent early 'COMPLETE' state
        return max(0, min(99, int(progress_pct * 100)))

    @classmethod
    def from_choices(cls, game_ids: list[int], choices: list[tuple[int, int]]) -> "RankMatrix":
        """
        Builds a new matrix object from a list of decisions, in the order they were made.
        Indices referring to unknown games or choices contradicting known information are skipped
        and collected in self.skipped

        Args:
            game_ids: list of integer Game IDs for building the graph.
            choices: list of (winner, loser) tuples representing the user's choices
        Returns:
            new_matrix: New RankMatrix object 
        """
        graph = cls(game_ids)
        for winner, loser in choices:
            if winner not in graph._index or loser not in graph._index or winner == loser:
                graph.skipped.append((winner, loser))
                continue
            try:
                graph.record(winner, loser)
            except ValueError:
                graph.skipped.append((winner, loser))
        return graph

    def record(self, winner: int, loser: int) -> bool:
        """
        Record the user's choice (winner > loser), as well as all implied wins/losses. 
        Adds the choice to the log if the record succeeds.

        Args:
            winner: Integer ID for the winning game
            loser: Integer ID for the losing game
        Returns:
            success: True if the matrix was updated by the choice, False if this was already known.
        Raises:
            ValueError: If loser > winner is already known or winner == loser
        """
        if winner == loser:
            raise ValueError("A game cannot be compared with itself")
        
        i, j = self._index[winner], self._index[loser]

        if self._matrix[j, i]:
            raise ValueError(f"{loser} is already preferred over {winner}")
        if self._matrix[i, j]:
            return False

        # Collect everything that beats the winner (predecessors)
        # and everything that the loser beats (successors)
        predecessors = np.append(np.flatnonzero(self._matrix[:, i]), i)
        successors = np.append(np.flatnonzero(self._matrix[j]), j)

        # Update the matrix with all wins/losses that this choice implies
        self._matrix[np.ix_(predecessors, successors)] = True

        self._log.append((winner, loser))
        return True

    def undo(self) -> Optional[tuple[int, int]]:
        """
        Reverses the most recent decision and rebuilds the matrix.
        
        Returns:
            last_choice: Most recent (winner, loser) tuple or None if no decisions have been recorded.
        """
        if not self._log:
            return None
        
        last = self._log.pop()
        self._rebuild()
        return last

    def _rebuild(self):
        """
        Rebuilds the matrix from the log.
        """
        current_log = list(self._log)
        self._log = []
        self._matrix[:] = False

        for w, l in current_log:
            self.record(w, l)

    def prefers(self, a: int, b: int) -> bool:
        return bool(self._matrix[self._index[a], self._index[b]])

    def get_scores(self) -> dict[int, float]:
        """
        Determines the current score for every game in the list for ranking.
        A game's 'score' is determined by wins - losses + winrate.

        Returns:
            scores: Dictionary of scores: {id: score}
        """

        wins = self._matrix.sum(axis=1)
        losses = self._matrix.sum(axis=0)
        degrees = wins + losses

        # Only score games that have been in at least one match
        indices = np.where(degrees > 0)[0]

        scores = {}
        for i in indices:
            score = wins[i] - losses[i] + (wins[i] / degrees[i])
            scores[self._ids[i]] = score

        return scores

    def get_next_pair(self) -> Optional[tuple[int, int]]:
        """
        Determines the next pair of items to display for comparison. Selects a node with the
        largest range of possible positions in the final ranking, then finds a second node
        whose midpoint is closest to that of the first and returns the pair.

        Returns:
            pair: tuple with the integer IDs for a pair of games or None if ranking is complete.
        """
        n = len(self._ids)
        if n < 2: return None
        i = j = 0

        wins = self._matrix.sum(axis=1)
        losses = self._matrix.sum(axis=0)
        degrees = wins + losses

        # Finds all unresolved pairs
        undecided_mask = ~(self._matrix | self._matrix.T)
        np.fill_diagonal(undecided_mask, False)

        # No unresolved pairs; ranking complete
        if not undecided_mask.any(): return None

        # Choose a target node with the highest uncertainty (fewest resolved matches)
        # Random choice if multiple nodes are tied
        min_deg = np.min(degrees)
        min_deg_nodes = np.where(degrees == min_deg)[0]
        i = np.random.choice(min_deg_nodes)

        i_mask = undecided_mask[i]
        if not np.any(i_mask):
            # Fallback: if we somehow pick an i with no undecided pairings,
            # return a random undecided pair.
            rows, cols = np.where(undecided_mask)
            index = np.random.randint(len(rows))
            return (self._ids[rows[index]], self._ids[cols[index]])

        # Calculate midpoint between best and worst rank for all nodes
        # Worst possible rank: n - wins
        # Best possible rank: losses + 1
        # Midpoint: (worst + best) / 2
        # Skip divide-by-two to stay in integer space
        midpoints = (n - wins) + (losses + 1)

        # Determine the midpoint distance between all other nodes and i
        distances = np.abs(midpoints - midpoints[i])

        # Find the minimum distance among all possible pairings
        min_dist = np.min(distances[i_mask])

        # Tiebreaker: find the degree of all nodes that share the minimum midpoint distance
        tiebreakers = np.where((distances == min_dist) & (i_mask), degrees, -1)

        # Find the maximum degree of those nodes and filter again
        max_deg = np.max(tiebreakers)
        max_deg_nodes = np.where((tiebreakers != -1) & (tiebreakers == max_deg))[0]

        if np.any(max_deg_nodes):
            # Choose one at random
            j = np.random.choice(max_deg_nodes)
        else:
            # Fallback: if no j was found, return a random undecided node w/r/t i
            j = np.random.choice(np.where(i_mask)[0])

        # Randomize the order to avoid positional bias
        if np.random.random() < 0.5:
            return (self._ids[i], self._ids[j])
        else:
            return (self._ids[j], self._ids[i])