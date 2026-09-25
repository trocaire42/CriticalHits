import reflex as rx
from app.components.builder.list_pane import list_pane
from app.components.builder.search_pane import search_pane
from app.components.navbar import navbar

def builder_page():
    return rx.vstack(
        navbar(),
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
        spacing="0"
    )