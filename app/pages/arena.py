import reflex as rx
from app.components.navbar import navbar
from app.components.arena.battle_pane import battle_pane
from app.components.arena.rank_pane import rank_pane
from app.state.arena_state import ArenaState
from app.state.auth_state import AuthState
from app.util import ROUTES

def arena_page():
    return rx.cond(
        AuthState.user_id,
        rx.vstack(
            navbar(ROUTES['battle']),
            rx.hstack(
                rank_pane(),
                battle_pane(),
                spacing="0",
                id="content-pane"
            ),
            spacing="0",
            id="main-container",
            on_mount=ArenaState.on_mount

        ),
        rx.center(
            rx.spinner(),
            id="main-container",
            on_mount=[
                lambda: AuthState.check_auth(ROUTES['battle']),
                ArenaState.on_mount
            ]
        )
    )