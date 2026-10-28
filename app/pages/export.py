import reflex as rx
from typing import Any
from app.models import Game
from app.util import DEFAULT_IMAGE
from app.state.export_state import ExportState

def export_view():
    return rx.box(
        rx.cond(
            ExportState.ready,
            rx.vstack(
                rx.grid(
                    rx.foreach(ExportState.ranked_list, _export_card),
                    columns="5",
                    spacing="0"
                ),
                id="export-container"
            ),
            rx.spinner()
        ),
        on_mount=ExportState.on_mount
    )

def _export_card(card_data: dict[str, Any]):
    rank: str = card_data['rank'].to(str)
    game: Game = card_data['game'].to(Game)

    return rx.box(
        rx.hstack(
            rx.image(
                src=rx.cond(
                    game.igdb_cover_id,
                    rx.get_upload_url(f"{game.igdb_cover_id}.jpg"),
                    DEFAULT_IMAGE
                ),
                class_name="export-card-img"
            ),
            rx.vstack(
                rx.text(f"#{rank}", class_name="export-card-rank-text"),
                rx.text(
                    game.title,
                    class_name="export-card-title"
                ),
                spacing="1",
                class_name="export-card-info"
            ),
            spacing="2",
            class_name="export-card"
        ),
        class_name="export-card-wrapper"
    )