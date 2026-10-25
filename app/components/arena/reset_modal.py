import reflex as rx
from app.state.arena_state import ArenaState

def reset_modal():
    return rx.cond(
        ArenaState.modal_active,
        rx.box(
            rx.vstack(
                rx.text(
                    "Reset All Progress?",
                    class_name="arena-modal-heading"
                ),
                rx.text(
                    "This will erase your leaderboard and start your ranking from scratch.",
                    class_name="arena-modal-message"
                ),
                rx.text(
                    "This action cannot be undone.",
                    class_name="arena-modal-message"
                ),
                rx.hstack(
                    rx.button(
                        "CANCEL",
                        variant="outline",
                        color_scheme="gray",
                        class_name="button-default-text",
                        on_click=ArenaState.close_modal
                    ),
                    rx.button(
                        "RESET ARENA",
                        variant="outline",
                        color_scheme="ruby",
                        class_name="button-default-text",
                        on_click=lambda: (ArenaState.close_modal(), ArenaState.reset_all_choices())
                    ),
                    spacing="6"
                ),
                spacing="3",
                class_name="arena-modal-center"
            ),
            class_name="arena-modal"
        )
    )