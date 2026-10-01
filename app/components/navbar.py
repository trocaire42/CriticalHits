import reflex as rx

def navbar(page: str):
    # Navigation button styling
    def _nav_item(label: str, route: str):
        is_active = route == page

        return rx.button(
            label,
            variant="ghost",
            color="#66f" if is_active else "white",
            border_bottom="2px solid #66f" if is_active else "2px solid transparent",
            disabled=is_active,
            opacity=1.0 if is_active else 0.7,
            on_click=lambda: rx.redirect(route),
            padding="5px 15px",
            size="3",
            font_family="Cinzel",
            _hover={
                "bg": "rgba(255,255,255,0.05)",
                "color": "white",
                "transform": "translateY(-1px)"
            }
        )
    
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon(tag="swords"),
                rx.text(
                    "CRITICAL HITS",
                    font_family="Cinzel",
                    font_weight="bold",
                    letter_spacing="2px",
                    font_size="1.5em",
                    _webkit_text_stroke="1px #d4af37",
                    paint_order="stroke fill"
                ),
                align="center",
                spacing="2"
            ),
            rx.spacer(),
            rx.hstack(
                _nav_item("HOME", "/"),
                _nav_item("COLLECTION", "/collection"),
                _nav_item("ARENA", "/arena"),
                spacing="4",
                align="center"
            ),
            width="100%",
            padding_x="40px",
            height="70px",
            align="center"
        ),
        width="100%",
        border_bottom="2px solid #333"
    )