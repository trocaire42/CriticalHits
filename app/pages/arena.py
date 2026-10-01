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
        width="100%",
        height="100vh",
        overflow="hidden",
        background="radial-gradient(circle, #1a1a2e 0%, #0f0f1a 100%)",
        color="white",
        spacing="0",
        on_mount=ArenaState.on_mount
    )