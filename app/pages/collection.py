import reflex as rx
from app.components.collection.list_pane import list_pane
from app.components.collection.search_pane import search_pane
from app.components.navbar import navbar
from app.state.collection_state import CollectionState

def collection_page():
    return rx.vstack(
        navbar("/collection"),
        rx.hstack(
            list_pane(),
            search_pane(),
            id="content-pane"
        ),
        spacing="0",
        on_mount=CollectionState.on_mount,
        id="main-container"
    )