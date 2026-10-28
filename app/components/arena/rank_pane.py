import reflex as rx
from typing import Any
from app.util import DEFAULT_IMAGE
from app.models import Game
from app.state.arena_state import ArenaState

def rank_pane():
    return rx.vstack(
        rx.heading(
            "LEADERBOARD",
            class_name="sidebar-heading sidebar-heading-text"
        ),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(ArenaState.ranked_results, _ranked_card),
                spacing="0"
            )
        ),
        spacing="1",
        id="sidebar"
    )

def _ranked_card(card_data: dict[str, Any]):
    rank: str = card_data['rank'].to(str)
    game: Game = card_data['game'].to(Game)
    change: str = card_data['change'].to(str)

    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(f"#{rank}", class_name="sidebar-card-rank-text"),
                class_name="sidebar-card-rank"
            ),
            rx.image(
                src=rx.cond(
                    game.igdb_cover_id,
                    rx.get_upload_url(f"{game.igdb_cover_id}.jpg"),
                    DEFAULT_IMAGE
                ),
                class_name="sidebar-card-img"
            ),
            rx.text(
                game.title,
                class_name="sidebar-card-title"
            ),
            class_name="sidebar-card"
        ),
        class_name=rx.cond(
            change == "",
            "sidebar-card-wrapper",
            f"sidebar-card-wrapper arena-card-{change}"
        )
    )