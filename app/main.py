import reflex as rx
from app.pages.landing import landing_page
from app.pages.collection import collection_page
from app.pages.arena import arena_page

app = rx.App(
    stylesheets=[
        "/style/theme.css",
        "/style/layout.css",
        "/style/text.css"
    ]
)
app.add_page(landing_page, route="/")
app.add_page(collection_page, route="/collection")
app.add_page(arena_page, route="/arena")