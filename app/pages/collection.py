import reflex as rx
from app.components.collection.list_pane import list_pane
from app.components.collection.search_pane import search_pane
from app.components.navbar import navbar
from app.state.collection_state import CollectionState
from app.state.auth_state import AuthState
from app.util import ROUTES

def collection_page():
    return rx.cond(
        AuthState.current_user_id,
        rx.vstack(
            navbar(ROUTES['list']),
            rx.hstack(
                list_pane(),
                search_pane(),
                spacing="0",
                id="content-pane"
            ),
            spacing="0",
            id="main-container",
            on_mount=[
                lambda: AuthState.check_auth(ROUTES['list']),
                CollectionState.on_mount
            ]
        ),
        rx.center(
            rx.spinner(),
            id="main-container",
            on_mount=lambda: AuthState.check_auth(ROUTES['list'])
        )
    )