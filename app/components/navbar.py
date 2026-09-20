import reflex as rx

def navbar():
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon(tag="swords"),
                rx.text(
                    "CRITICAL HITS",
                    font_weight="bold",
                    letter_spacing="2px",
                    font_size="1.5em"
                ),
                align="center",
                spacing="2"
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "Home",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=lambda: rx.redirect("/")
                ),
                rx.button(
                    "Builder",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=lambda: rx.redirect("/builder")
                ),
                rx.button(
                    "Ranker",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=lambda: rx.redirect("/rank"),
                    disabled=True # TODO: Remove this line once battle page is ready
                ),
                spacing="6"
            ),
            width="100%",
            padding_x="40px",
            height="70px",
            align="center"
        ),
        width="100%",
        border_bottom="2px solid #333"
    )