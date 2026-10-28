import reflex as rx
from app.state.auth_state import AuthState

def landing_page():
    return rx.center(
        rx.vstack(
            rx.vstack(
                rx.heading(
                    rx.hstack(
                        rx.text("CRITICAL HITS"),
                        rx.text("!", font_style="italic"),
                        spacing="0"
                    ),
                    class_name="landing-title"
                ),
                rx.text(
                    "THE BATTLE FOR #1", 
                    class_name="landing-tagline"
                ),
                align="center",
                spacing="4"
            ),
            rx.vstack(
                rx.button(
                    "BUILD YOUR COLLECTION",
                    variant="outline",
                    color_scheme="blue",
                    on_click=lambda: rx.redirect("/collection"),
                    class_name="landing-button button-default-text"
                ),
                rx.button(
                    "ENTER THE ARENA",
                    variant="outline",
                    color_scheme="blue",
                    on_click=lambda: rx.redirect("/arena"),
                    class_name="landing-button button-default-text"
                ),
                spacing="4"
            ),
            rx.vstack(
                rx.divider(),
                rx.text(
                    "v0.1 | Developed by trocaire",
                    class_name="landing-footer-text"
                ),
                align="center",
                spacing="2"
            ),
            align="center",
            spacing="4"
        ),
        id="main-container",
        on_mount=AuthState.check_auth
    )