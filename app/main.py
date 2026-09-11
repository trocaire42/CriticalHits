import reflex as rx
from .pages.landing import landing_page
from .pages.builder import builder_page

app = rx.App()
app.add_page(landing_page, route="/")
app.add_page(builder_page, route="/builder")