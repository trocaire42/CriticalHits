import reflex as rx
from app.components.navbar import navbar
from app.components.arena.battle_pane import battle_pane
from app.components.arena.rank_pane import rank_pane
from app.state.arena_state import ArenaState

def arena_page():
    return rx.vstack(
        navbar("/arena"),
        rx.hstack(
            rank_pane(),
            battle_pane(),
            width="100%",
            align_items="stretch",
            flex="1",
            overflow="hidden"
        ),
        id="main-container",
        spacing="0",
        on_mount=ArenaState.on_mount
    )