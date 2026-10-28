import reflex as rx
from app.models import Game
from app.util import DEFAULT_IMAGE, ROUTES
from app.state.arena_state import ArenaState, UIStatus
from app.components.arena.reset_modal import reset_modal

def battle_pane():
    return rx.vstack(
        # 'Reset All' modal
        reset_modal(),

        # Progress Bar Area
        rx.box(
            rx.progress(
                value=ArenaState.progress,
                color_scheme="iris",
                size="3",
                radius="full",
                variant="classic"
            ),
            class_name="arena-progress-wrapper"
        ),
        rx.match(
            ArenaState.ui_state,
            (UIStatus.WINNER, _winner_anims()),
            (UIStatus.LOADING, _loading_screen()),
            (UIStatus.TOO_FEW, _need_more()),
            (UIStatus.READY, _battle_ready()),
            (UIStatus.COMPLETE, _ranking_complete()),
            (UIStatus.ERROR, _arena_error())
        ),
        id="center-pane"
    ),

def _loading_screen():
    return rx.vstack(
        rx.heading("Preparing the next match...", class_name="arena-heading"),
        rx.spinner(size="3"),
        spacing="2",
        class_name="arena-battle-pane"
    )

def _need_more():
    return rx.vstack(
        rx.heading("Unable to enter the Arena", class_name="arena-heading"),
        rx.text(
            "The Arena requires at least five games to play.",
            class_name="arena-explain-text"
        ),
        rx.text(
            "Add more to your ",
            rx.link(
                "Collection",
                href=ROUTES['list'],
                class_name="link-default"
            ),
            " to continue.",
            class_name="arena-explain-text"
        ),
        spacing="1",
        class_name="arena-battle-pane"
    )

def _battle_ready():
    return rx.vstack(
        rx.text(f"Match {ArenaState.choice_count + 1}", class_name="arena-match-count"),
        rx.hstack(
            rx.box(
                _battle_card(ArenaState.current_pair[0]),
                class_name="arena-card-wrapper arena-card-enter-left",
                on_click=lambda: ArenaState.choose_winner(0)
            ),
            rx.text("VS", class_name="arena-vs-text"),
            rx.box(
                _battle_card(ArenaState.current_pair[1]),
                class_name="arena-card-wrapper arena-card-enter-right",
                on_click=lambda: ArenaState.choose_winner(1)
            ),
            spacing="4",
            class_name="arena-battle-wrapper"
        ),
        rx.vstack(
            rx.text("Tap a card to choose the winner", class_name="arena-explain-text"),
            rx.text(
                "Forgot something? Add more to your ",
                rx.link(
                    "Collection",
                    href=ROUTES['list'],
                    class_name="link-default"
                ),
                class_name="arena-explain-text"
            ),
            rx.hstack(
                rx.hover_card.root(
                    rx.hover_card.trigger(
                        rx.button(
                            rx.icon(tag="undo-2", color="gray"),
                            variant="ghost",
                            color_scheme="gray",
                            disabled=ArenaState.prev_pair == None,
                            on_click=ArenaState.undo_last_choice
                        ),
                    ),
                    rx.hover_card.content(
                        rx.cond(
                            ArenaState.prev_pair == None,
                            rx.text("Nothing to Undo", class_name="arena-tooltip"),
                            rx.vstack(
                                rx.text("Undo Last Choice:", class_name="arena-tooltip"),
                                rx.separator(width="75%"),
                                rx.hstack(
                                    rx.text("Win: ", class_name="arena-tooltip"),
                                    rx.text(ArenaState.prev_pair[0].title, class_name="arena-tooltip"),
                                    width="100%"
                                ),
                                rx.hstack(
                                    rx.text("Loss: ", class_name="arena-tooltip"),
                                    rx.text(ArenaState.prev_pair[1].title, class_name="arena-tooltip"),
                                    width="100%"
                                ),
                                spacing="1",
                                class_name="arena-tooltip-wrapper"
                            )
                        ),
                        align="center",
                        side="top"
                    )
                ),
                rx.hover_card.root(
                    rx.hover_card.trigger(
                        rx.button(
                            rx.icon(tag="list-restart", color="gray"),
                            variant="ghost",
                            color_scheme="gray",
                            on_click=ArenaState.open_modal
                        ),
                    ),
                    rx.hover_card.content(
                        rx.vstack(
                            rx.text("Reset ALL Choices", class_name="arena-tooltip")
                        ),
                        align="center",
                        side="top"
                    )
                ),
                spacing="3"
            ),
            spacing="2",
            align_items="center"
        ),
        class_name="arena-battle-pane"
    )

def _winner_anims():
    return rx.vstack(
        rx.hstack(
            rx.box(
                _battle_card(ArenaState.current_pair[0]),
                class_name=rx.cond(
                    ArenaState.winner_index == 0,
                    "arena-card-wrapper arena-card-win",
                    "arena-card-wrapper arena-card-lose-l"
                )
            ),
            rx.text("VS", class_name="arena-vs-text arena-vs-fade"),
            rx.box(
                _battle_card(ArenaState.current_pair[1]),
                class_name=rx.cond(
                    ArenaState.winner_index == 1,
                    "arena-card-wrapper arena-card-win",
                    "arena-card-wrapper arena-card-lose-r"
                )
            ),
            spacing="4",
            class_name="arena-battle-wrapper"
        ),
        class_name="arena-battle-pane"
    )

def _battle_card(game: Game):
    return rx.vstack(
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
    )

def _ranking_complete():
    return rx.vstack(
        rx.heading("Ranking Complete!", class_name="arena-done-text"),
        rx.text("Export Leaderboard:", class_name="arena-heading"),
        rx.button(
            "Text",
            variant="outline",
            color_scheme="blue",
            loading=ArenaState.is_exporting,
            on_click=ArenaState.export_text,
            class_name="arena-export-button button-default-text"
        ),
        rx.foreach([10, 25, 50, 100, 150, 200, 500, 1000], _export_button),
        rx.hstack(
            rx.hover_card.root(
                rx.hover_card.trigger(
                    rx.button(
                        rx.icon(tag="undo-2", color="gray"),
                        variant="ghost",
                        color_scheme="gray",
                        disabled=ArenaState.prev_pair == None,
                        on_click=ArenaState.undo_last_choice
                    ),
                ),
                rx.hover_card.content(
                    rx.cond(
                        ArenaState.prev_pair == None,
                        rx.text("Nothing to Undo", class_name="arena-tooltip"),
                        rx.vstack(
                            rx.text("Undo Last Choice:", class_name="arena-tooltip"),
                            rx.separator(width="75%"),
                            rx.hstack(
                                rx.text("Win: ", class_name="arena-tooltip"),
                                rx.text(ArenaState.prev_pair[0].title, class_name="arena-tooltip"),
                                width="100%"
                            ),
                            rx.hstack(
                                rx.text("Loss: ", class_name="arena-tooltip"),
                                rx.text(ArenaState.prev_pair[1].title, class_name="arena-tooltip"),
                                width="100%"
                            ),
                            spacing="1",
                            class_name="arena-tooltip-wrapper"
                        )
                    ),
                    align="center",
                    side="top"
                )
            ),
            rx.hover_card.root(
                rx.hover_card.trigger(
                    rx.button(
                        rx.icon(tag="list-restart", color="gray"),
                        variant="ghost",
                        color_scheme="gray",
                        on_click=ArenaState.open_modal
                    ),
                ),
                rx.hover_card.content(
                    rx.vstack(
                        rx.text("Reset ALL Choices", class_name="arena-tooltip")
                    ),
                    align="center",
                    side="top"
                )
            ),
            spacing="3"
        ),
        spacing="4",
        class_name="arena-battle-pane"
    )

def _export_button(size):
    return rx.cond(
        ArenaState.ranked_results.length() >= size,
        rx.button(
            f"Top {size} Image",
            variant="outline",
            color_scheme="blue",
            loading=ArenaState.is_exporting,
            on_click=lambda: ArenaState.export_image(size),
            class_name="arena-export-button button-default-text"
        )
    )

def _arena_error():
    return rx.vstack(
        rx.hstack(
            rx.icon(tag="triangle-alert", color="orange"),
            rx.heading("Error: Unable to Load Arena", class_name="arena-heading"),
            rx.icon(tag="triangle-alert", color="orange"),
            align_items="center",
            spacing="2"
        ),
        rx.button(
            "REFRESH",
            variant="outline",
            color_scheme="red",
            on_click=ArenaState.on_mount,
            class_name="button-default-text"
        ),
        spacing="2",
        class_name="arena-battle-pane"
    )