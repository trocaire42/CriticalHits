import reflex as rx

def navbar(page: str):
    # Navigation button styling
    def _nav_item(label: str, route: str):
        is_active = route == page

        return rx.button(
            label,
            variant="ghost",
            size="3",
            disabled=is_active,
            on_click=lambda: rx.redirect(route),
            class_name=rx.cond(is_active, "navbar-button button-active", "navbar-button")
        )
    
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon(tag="swords"),
                rx.text(
                    "CRITICAL HITS",
                    class_name="navbar-title"
                ),
                align_items="center",
                spacing="2"
            ),
            rx.spacer(),
            rx.hstack(
                _nav_item("HOME", "/"),
                _nav_item("COLLECTION", "/collection"),
                _nav_item("ARENA", "/arena"),
                spacing="4",
            ),
            class_name="navbar-content"
        ),
        id="navbar"
    )