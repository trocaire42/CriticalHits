import reflex as rx
from typing import Any
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

def _ranked_card(game: dict[str, Any]):
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(f"#{game['rank']}", class_name="sidebar-card-rank-text"),
                class_name="sidebar-card-rank"
            ),
            rx.image(
                src=rx.cond(
                    game.get("img"),
                    rx.get_upload_url(game["img"]),
                    "/images/noimg.jpg"
                ),
                class_name="sidebar-card-img"
            ),
            rx.text(
                game["title"],
                class_name="sidebar-card-title"
            ),
            class_name="sidebar-card"
        ),
        class_name="sidebar-card-wrapper"
    )