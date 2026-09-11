import reflex as rx
from app.state.builder_state import BuilderState

def search_pane():
    return rx.vstack(
        # Search Form
        rx.form(
            rx.hstack(
                rx.hstack(
                    rx.input(
                        placeholder="Search for a game...",
                        on_change=BuilderState.set_search_query,
                        width="450px",
                        height="100%",
                        border_top_right_radius="0",
                        border_bottom_right_radius="0",
                    ),
                    rx.tooltip(
                        rx.button(
                            rx.icon(tag="filter", size=14),
                            on_click=BuilderState.toggle_search_mode,
                            type="button",
                            variant="soft",
                            height="100%",
                            border_top_left_radius="0",
                            border_bottom_left_radius="0",
                            color_scheme=rx.cond(BuilderState.search_exact, "green", "gray"),
                        ),
                        content=rx.cond(
                            BuilderState.search_exact,
                            "Click to disable Exact Search",
                            "Click to enable Exact Search",
                        ),
                    ),
                    spacing="0",
                    height="40px",
                    align_items="stretch",
                ),
                rx.button(
                    rx.icon(tag="search", size=14),
                    type="submit",
                    size="3",
                    loading=BuilderState.is_loading
                ),
                width="100%",
                justify="center",
                align_items="center",
                padding_top="40px",
            ),
            on_submit=BuilderState.search_new,
            width="100%",
            justify="center",
        ),
        rx.text(
            "Search results powered by ",
            rx.link(
                "RAWG",
                href="https://rawg.io",
                target="_blank",
                color="gray",
                text_decoration="underline"
            ),
            font_size="0.8em",
            color="gray",
            opacity="0.6",
        ),
        rx.divider(margin_y="10px", width="100%"),
    
        # Results Section
        rx.scroll_area(
            rx.vstack(
                rx.foreach(BuilderState.search_results, _search_result_card),
                width="100%",
                spacing="0",
            ),
    
            rx.center(
                rx.cond(
                    BuilderState.search_more,
                    rx.button(
                        "Load More",
                        on_click=BuilderState.search_continue,
                        loading=BuilderState.is_loading,
                        size="4",
                    ),
                    rx.text("No more results to show.", color="gray", padding="20px")
                ),
                width="100%",
            ),
            width="85%",
            flex="1",
        ),
        width="100%",
        height="100%",
        padding_bottom="10px",
        align_items="center",
        overflow="hidden",
    ),

def _search_result_card(game: dict):
    return rx.hstack(
        rx.image(
            src=game['cover'],
            width="80px", 
            height="80px", 
            object_fit="cover", 
            border_radius="4px"
        ),
        rx.vstack(
            rx.text(game["title"], font_weight="bold", font_size="1.5em"),
            rx.text(f"{game['year']} | {game['platform']}", font_size="1em", color="gray"),
            align_items="start",
            spacing="0",
        ),
        rx.spacer(),
        rx.button(
            rx.cond(
                game["active"],
                rx.icon(tag="minus", size=18, color="red"),
                rx.icon(tag="plus", size=18, color="green"),
            ),
            on_click=lambda: BuilderState.toggle_game(game),
            color_scheme=rx.cond(game["active"], "red", "green"),
            variant="soft",
            size="3",
            loading=BuilderState.is_loading,
        ),
        width="100%",
        padding="10px 20px",
        border_bottom="1px solid #222",
        align_items="center",
    )