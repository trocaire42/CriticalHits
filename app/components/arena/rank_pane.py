import reflex as rx
from app.state.arena_state import ArenaState

def rank_pane():
    return rx.scroll_area(
        rx.vstack(
            rx.foreach(ArenaState.ranked_results, _ranked_card),
            width="100%",
            spacing="0"
        ),
        width="400px",
        height="100%",
        padding_left="10px",
        border_right="1px solid #444"
    )

def _ranked_card(game:dict):
    return rx.box(
        rx.hstack(
            rx.text(f"#{game['rank']}", color="gold", font_weight="bold", width="60px", padding_x="10px", text_align="right"),
            rx.image(
                src=rx.cond(
                    game.get("img"),
                    rx.get_upload_url(game["img"]),
                    "/noimg.jpg"
                ),
                width="35px",
                height="50px",
                object_fit="contain",
                border_radius="2px"
            ),
            rx.text(
                game["title"],
                font_family="Cinzel",
                font_size="1em",
                flex="1",
                letter_spacing="1px"
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