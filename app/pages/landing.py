import reflex as rx

def landing_page():
    return rx.center(
        rx.vstack(
            # --- Title Section ---
            rx.vstack(
                rx.heading(
                    rx.hstack(
                        rx.text("CRITICAL HITS", letter_spacing="8px"),
                        rx.text("!", font_style="italic"),
                        align="baseline",
                        spacing="0"
                    ),
                    size="9", 
                    font_family="Cinzel",
                    color="white",
                    _webkit_text_stroke="2px #d4af37",
                    paint_order="stroke fill"
                ),
                rx.text(
                    "A DIGITAL BATTLE TO REACH #1", 
                    font_family="Cinzel",
                    font_size="0.8em",
                    letter_spacing="4px",
                    color="gray",
                    margin_bottom="40px"
                ),
                align="center",
                spacing="0"
            ),

            # --- Vertical Menu Section ---
            rx.vstack(
                rx.button(
                    "BUILD YOUR COLLECTION",
                    width="320px",
                    height="60px",
                    font_family="Cinzel",
                    font_size="1.1em",
                    letter_spacing="2px",
                    variant="outline",
                    color_scheme="blue",
                    on_click=lambda: rx.redirect("/builder"),
                    _hover={
                        "bg": "rgba(255, 255, 255, 0.1)",
                        "transform": "scale(1.05)",
                        "transition": "all 0.2s ease-in-out"
                    }
                ),
                
                rx.button(
                    "ENTER THE ARENA",
                    width="320px",
                    height="60px",
                    font_family="Cinzel",
                    font_size="1.1em",
                    letter_spacing="2px",
                    variant="outline",
                    color_scheme="blue",
                    disabled=True,
                    opacity=0.5,
                    _hover={
                        "bg": "rgba(255, 255, 255, 0.1)",
                        "transform": "scale(1.05)",
                        "transition": "all 0.2s ease-in-out"
                    }
                ),
                spacing="4",
                align="center"
            ),

            # --- Footer Decoration ---
            rx.vstack(
                rx.divider(width="100px", border_color="gray", margin_top="20px"),
                rx.text(
                    "v0.1", 
                    font_size="0.6em", 
                    color="gray", 
                    letter_spacing="2px"
                ),
                align="center",
                spacing="2",
                opacity="0.5"
            ),
            align="center",
            spacing="0"
        ),
        width="100%",
        height="100vh",
        background="radial-gradient(circle, #1a1a2e 0%, #0f0f1a 100%)"
    )