import reflex as rx
from typing import Any
from app.state.arena_state import ArenaState

def battle_pane():
    return rx.vstack(
        # Progress Bar Area
        rx.vstack(
            rx.progress(value=ArenaState.completion, width="100%", color_scheme="yellow"),
            width="100%",
            align_items="center",
            padding_bottom="10px",
        ),
        rx.cond(
            # Check if we have a pair to display
            ArenaState.current_pair.length() == 2,
            rx.vstack(
                rx.hstack(
                    rx.box(
                        _battle_card(ArenaState.current_pair[0]),
                        on_click=lambda: ArenaState.handle_selection(
                            ArenaState.current_pair[0]["id"], 
                            ArenaState.current_pair[1]["id"]
                        ),
                        height="100%"
                    ),
                    rx.text("VS", font_family="Cinzel", color="gold", font_size="2rem"),
                    rx.box(
                        _battle_card(ArenaState.current_pair[1]),
                        on_click=lambda: ArenaState.handle_selection(
                            ArenaState.current_pair[1]["id"], 
                            ArenaState.current_pair[0]["id"]
                        ),
                        height="100%"
                    ),
                    spacing="4",
                    align_items="center",
                    width="100%",
                    height="550px",
                    justify_content="center"
                ),
                rx.vstack(
                    rx.text("Tap the winner to decide"),
                    rx.text(
                        "Forgot something? Add more to your ",
                        rx.link(
                            "Collection",
                            href="/collection",
                            color="gray",
                            text_decoration="underline"
                        )
                    ),
                    font_family="Cinzel",
                    color="gray",
                    font_size="1rem",
                    align_items="center"
                ),
                width="100%",
                height="100%",
                justify_content="center",
                align_items="center"
            ),
            # If no more pairs (Tournament finished)
            rx.vstack(
                rx.heading("Tournament Complete!", font_family="Cinzel", color="gold"),
                padding="4rem",
                align_items="center",
            ),
        ),
        flex="1",
        padding="3rem",
        align_items="center"
    ),

def _battle_card(game: dict[str, Any]):
    return rx.box(
        rx.vstack(
            # Cover Image
            rx.image(
                src=rx.cond(
                    game.get("img"),
                    rx.get_upload_url(game["img"]),
                    "/noimg.jpg"
                ),
                width="264px",
                height="374px",
                object_fit="cover",
                border_radius="5px",
                box_shadow="0 10px 25px -5px rgba(0, 0, 0, 0.4)",
            ),
            # Title and Year
            rx.vstack(
                rx.text(
                    game["title"],
                    font_family="Cinzel",
                    font_size="1.5rem",
                    color="gold",
                    text_align="center",
                    padding_top="15px",
                ),
                rx.text(
                    f"{game['year']}",
                    font_size="0.9rem",
                    color="gray",
                    text_align="center",
                ),
                align_items="center",
            ),
            align_items="center",
            width="100%",
            height="100%",
            justify_content="space-between",
            padding_bottom="10px"
        ),
        width="400px",
        height="100%",
        padding="15px",
        background="rgba(30, 30, 30, 0.8)",
        border="1px solid rgba(212, 175, 55, 0.3)",
        border_radius="10px",
        transition="transform 0.2s ease-in-out",
        _hover={"transform": "scale(1.05)", "border_color": "gold"},
    )