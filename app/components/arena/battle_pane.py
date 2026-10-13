import reflex as rx
from app.models import Game
from app.util import DEFAULT_IMAGE
from app.state.arena_state import ArenaState, UIStatus

def battle_pane():
    return rx.vstack(
        # Progress Bar Area
        rx.box(
            rx.progress(
                value=ArenaState.completion,
                color_scheme="iris",
                size="3",
                radius="full",
                variant="classic"
            ),
            class_name="arena-progress-wrapper"
        ),
        rx.match(
            # Check if we have a pair to display
            ArenaState.ui_state,
            (UIStatus.READY,
                rx.vstack(
                    rx.hstack(
                        _battle_card(ArenaState.current_pair[0], ArenaState.current_pair[1]),
                        rx.text("VS", class_name="arena-vs-text"),
                        _battle_card(ArenaState.current_pair[1], ArenaState.current_pair[0]),

                        spacing="4",
                        class_name="arena-battle-wrapper"
                    ),
                    rx.vstack(
                        rx.text("Tap a card to choose the winner", class_name="arena-explain-text"),
                        rx.text(
                            "Forgot something? Add more to your ",
                            rx.link(
                                "Collection",
                                href="/collection",
                                class_name="link-default"
                            ),
                            class_name="arena-explain-text"
                        ),
                        align_items="center"
                    ),
                    class_name="arena-battle-pane"
                ),
            ),
            # TODO: other conditionals (loading state, error state, list too small, tournament complete)
            (UIStatus.COMPLETE,
                rx.vstack(
                    rx.heading("Ranking Complete!", font_family="Cinzel", color="gold"),
                    padding="4rem",
                    align_items="center",
                ),
            )
        ),
        id="center-pane"
    ),

def _battle_card(game: Game, opponent: Game):
    return rx.box(
        rx.vstack(
            # Cover Image
            rx.image(
                src=rx.cond(
                    game.igdb_cover_id,
                    rx.get_upload_url(f"{game.igdb_cover_id}.jpg"),
                    DEFAULT_IMAGE
                ),
                class_name="arena-card-image"
            ),
            # Title and Year
            rx.vstack(
                rx.text(
                    game.title,
                    class_name="arena-card-title"
                ),
                rx.text(
                    rx.cond(game.release_year, game.release_year, "N/A"),
                    class_name="arena-card-text"
                ),
                spacing="1",
                class_name="arena-card-detail-wrapper"
            ),
            class_name="arena-card"
        ),
        class_name="arena-card-wrapper",
        on_click=lambda: ArenaState.handle_selection(game.id, opponent.id)
    )