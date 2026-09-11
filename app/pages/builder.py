import reflex as rx
from app.components.builder.list_pane import list_pane
from app.components.builder.search_pane import search_pane

def builder_page():
    return rx.hstack(
        list_pane(),
        search_pane(),
        width="100%",
        height="100vh",
        overflow="hidden",
        background="#1a1a1a",
        color="white",
    )