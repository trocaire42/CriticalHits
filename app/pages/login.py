import reflex as rx
from app.state.auth_state import AuthState

def login_page():
    return rx.center(
        rx.vstack(
            rx.text("Logging in...", class_name="login-message"),
            rx.spinner()
        ),
        on_mount=AuthState.on_mount,
        id="main-container"
    )