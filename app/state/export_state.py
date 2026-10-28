import reflex as rx
import logging
from typing import Any
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.models import User
from app.services.rank_matrix import RankMatrix

logger = logging.getLogger(__name__)

class ExportState(rx.State):
    ranked_list: list[dict[str, Any]] = []
    ready: bool = False

    async def on_mount(self):
        self.ready = False
        yield

        await self._build_export(self.uuid, int(self.count))
        self.ready = True



    async def _build_export(self, uuid: str, count: int):
        try:
            async with rx.asession() as session:
                # Gets a list of all games and choices associated with the user
                query = (
                    select(User)
                    .where(User.uuid == uuid)
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

                # Builds the win/loss matrix
                rank_matrix = RankMatrix.from_choices(game_ids, choices)

                # Sorts the games list by score
                scores = rank_matrix.get_scores()
                game_list = list(user.collection)
                game_list.sort(key=lambda x: scores[x.id], reverse=True)

                capped_count = min(count, len(game_list))

                self.ranked_list = [{'rank': f"{i + 1:03}", 'game': game_list[i]} for i in range(capped_count)]
        except Exception as e:
            logger.error(f"[!] Database error in export generation: {e}")
            self.ranked_list = []