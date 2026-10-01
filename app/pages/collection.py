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
        on_mount=CollectionState.on_mount
    )