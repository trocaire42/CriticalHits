import reflex as rx
from app.pages.landing import landing_page
from app.pages.builder import builder_page

app = rx.App(stylesheets=["https://fonts.googleapis.com/css2?family=Cinzel:wght@400..900&display=swap"])
app.add_page(landing_page, route="/")
app.add_page(builder_page, route="/builder")