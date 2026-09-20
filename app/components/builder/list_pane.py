import reflex as rx
from app.state.builder_state import BuilderState

def list_pane():
    return rx.vstack(
        rx.heading(f"My List ({BuilderState.added_games.length()})", size="4"),
        rx.divider(),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(BuilderState.added_games, _sidebar_card),
                width="100%",
                spacing="0"
            ),
            flex="1",
            width="100%"
        ),
        width="300px",
        height="100%",
        padding="20px 0 0 10px",
        border_right="1px solid #444",
        on_mount=BuilderState.on_mount
    )

def _sidebar_card(game: dict):
    return rx.hstack(
        rx.cond(
            # Checks if an image was retrieved from IGDB and displays a placeholder if not
            game["img"],
            rx.image(
                src=rx.get_upload_url(game["img"]),
                width="45px",
                height="64px",
                object_fit="contain",
                border_radius="2px"
            ),
            rx.image(
                src="/noimg.jpg",
                width="45px",
                height="64px",
                object_fit="contain",
                border_radius="2px"
            )
        ),
        rx.text(game["title"], font_size="0.95em", flex="1"),
        rx.button(
            rx.icon(tag="trash", size=16, color="red"),
            on_click=lambda: BuilderState.toggle_game(game),
            variant="ghost",
            color_scheme="gray",
            padding="5px",
            size="1",
            loading=BuilderState.is_loading
        ),
        width="100%",
        spacing="2",
        padding="10px 20px 10px 0",
        align_items="center",
        border_bottom="1px solid #333",
        _hover={"bg": "rgba(255,255,255,0.05)"}
    )