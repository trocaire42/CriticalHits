import reflex as rx

def landing_page():
    return rx.center(
        rx.vstack(
            rx.heading("Critical Hits", size="9", margin_bottom="20px"),
            rx.text("Your favorite games battle it out for the #1 spot", color="gray"),
            rx.hstack(
                rx.button(
                    "Build Your List", 
                    size="3", 
                    on_click=lambda: rx.redirect("/builder"),
                    color_scheme="blue"
                ),
                rx.button(
                    "Start Ranking", 
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