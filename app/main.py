import reflex as rx
from app.pages.landing import landing_page
from app.pages.collection import collection_page
from app.pages.arena import arena_page
from app.pages.login import login_page
from app.util import ROUTES

app = rx.App(
    stylesheets=[
        "/style/theme.css",
        "/style/layout.css",
        "/style/text.css",
        "/style/anim.css"
    ]
)
app.add_page(landing_page, route=ROUTES["home"])
app.add_page(collection_page, route=ROUTES["list"])
app.add_page(arena_page, route=ROUTES["battle"])
app.add_page(login_page, route=ROUTES["login"])