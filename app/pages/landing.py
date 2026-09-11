import reflex as rx

def landing_page():
    return rx.center(
        rx.vstack(
            rx.heading("Game Ranker", size="9", margin_bottom="20px"),
            rx.text("Organize your collection by preference.", color="gray"),
            rx.hstack(
                rx.button(
                    "New Session", 
                    size="3", 
                    on_click=lambda: rx.redirect("/builder"),
                    color_scheme="blue"
                ),
                rx.button(
                    "Load Session", 
                    size="3", 
                    color_scheme="gray",
                    disabled=True # Logic for later
                ),
                spacing="4",
                margin_top="30px",
            ),
            spacing="4",
            align_items="center",
        ),
        width="100%",
        height="100vh",
    )