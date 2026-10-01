import reflex as rx
from app.state.collection_state import CollectionState

def list_pane():
    return rx.vstack(
        rx.heading(
            f"MY COLLECTION ({CollectionState.added_games.length()})",
            size="5",
            letter_spacing="2px",
            font_family="Cinzel",
            text_align="center",
            width="100%"
        ),
        rx.divider(),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(CollectionState.added_games, _sidebar_card),
                width="100%",
                spacing="0"
            ),
            flex="1",
            width="100%"
        ),
        width="450px",
        height="100%",
        padding="20px 0 0 10px",
        border_right="1px solid #444"
    )

def _sidebar_card(game: dict):
    return rx.box(
        rx.hstack(
            rx.image(
                src=rx.cond(
                    game["img"],
                    rx.get_upload_url(game["img"]),
                    "/noimg.jpg"
                ),
                width="45px",
                height="64px",
                object_fit="contain",
                border_radius="2px"
            ),
            rx.text(
                game["title"],
                font_family="Cinzel",
                font_size="1.2em",
                flex="1",
                letter_spacing="1px"
            ),
            rx.button(
                rx.icon(tag="trash-2", size=16, color="red"),
                on_click=lambda: CollectionState.toggle_game(game),
                variant="ghost",
                color_scheme="gray",
                padding="8px",
                size="1",
                loading=CollectionState.is_loading
            ),
            width="100%",
            spacing="2",
            padding="10px 20px 10px 10px",
            align_items="center",
            border_bottom="1px solid #333",
            _hover={
                "bg": "rgba(255, 255, 255, 0.1)",
                "transform": "scale(1.03)",
                "transition": "all 0.2s ease-in-out"
            }
        ),
        width="100%",
        overflow="hidden",
        position="relative"
    )