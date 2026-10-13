import reflex as rx
from app.util import DEFAULT_IMAGE
from app.models import Game
from app.state.collection_state import CollectionState

def list_pane():
    return rx.vstack(
        rx.heading(
            f"COLLECTION ({CollectionState.added_games.length()})",
            class_name="sidebar-heading sidebar-heading-text"
        ),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(CollectionState.added_games, _sidebar_card),
                spacing="0"
            )
        ),
        spacing="1",
        id="sidebar"
    )

def _sidebar_card(game: Game):
    return rx.box(
        rx.hstack(
            rx.cond(
                CollectionState.synced_ids.contains(game.id),
                rx.image(
                    src=rx.cond(
                        game.igdb_cover_id,
                        rx.get_upload_url(f"{game.igdb_cover_id}.jpg"),
                        DEFAULT_IMAGE
                    ),
                    class_name="sidebar-card-img"
                ),
                rx.box(
                    rx.spinner(size="2"),
                    class_name="sidebar-card-img-loading"
                )
            ),
            rx.text(
                game.title,
                class_name="sidebar-card-title"
            ),
            rx.box(
                rx.button(
                    rx.icon(tag="trash-2", size=20, color="red"),
                    on_click=lambda: CollectionState.toggle_game(game),
                    variant="ghost",
                    color_scheme="gray",
                    loading=CollectionState.is_loading
                ),
                class_name="sidebar-card-delete"
            ),
            class_name="sidebar-card"
        ),
        class_name="sidebar-card-wrapper"
    )