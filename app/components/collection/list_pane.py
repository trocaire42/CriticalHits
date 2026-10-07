import reflex as rx
from typing import Any
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

def _sidebar_card(game: dict[str, Any]):
    return rx.box(
        rx.hstack(
            rx.cond(
                CollectionState.synced_ids.contains(game.get("id", 0)),
                rx.image(
                    src=rx.cond(
                        game.get("img"),
                        rx.get_upload_url(game["img"]),
                        "/images/noimg.jpg"
                    ),
                    class_name="sidebar-card-img"
                ),
                rx.box(
                    rx.spinner(size="2"),
                    class_name="sidebar-card-img-loading"
                )
            ),
            rx.text(
                game["title"],
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