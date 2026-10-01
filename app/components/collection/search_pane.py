import reflex as rx
from app.state.collection_state import CollectionState

def search_pane():
    return rx.vstack(
        # Search Form
        rx.form(
            rx.hstack(
                rx.input(
                    placeholder="Search for a game...",
                    on_change=CollectionState.set_search_query,
                    width="450px",
                    height="40px"
                ),
                rx.button(
                    rx.icon(tag="search", size=14),
                    type="submit",
                    size="3",
                    loading=CollectionState.is_loading
                ),
                width="100%",
                justify="center",
                align_items="center",
                padding_top="25px"
            ),
            on_submit=CollectionState.search_new,
            width="100%",
            justify="center"
        ),
        rx.text(
            "Search results powered by ",
            rx.link(
                "IGDB",
                href="https://www.igdb.com",
                target="_blank",
                color="gray",
                text_decoration="underline"
            ),
            font_size="0.8em",
            color="gray",
            opacity="0.6"
        ),
        rx.divider(margin_y="10px", width="100%"),
    
        # Results Section
        rx.scroll_area(
            rx.vstack(
                rx.cond(
                    CollectionState.search_key > 0,
                    rx.foreach(CollectionState.search_results, _search_result_card),
                    rx.vstack(
                        rx.icon(tag="search", size=40, color="gray"),
                        rx.text("Search for a game to build your collection", color="gray"),
                        spacing="2",
                        padding_top="20px",
                        width="100%",
                        align_items="center"
                    )
                ),
                width="100%",
                spacing="0"
            ),
    
            rx.center(
                rx.cond(
                    CollectionState.search_key > 0,
                    rx.cond(
                        CollectionState.search_more,
                        rx.button(
                            "Load More",
                            on_click=CollectionState.search_continue,
                            loading=CollectionState.is_loading,
                            size="4",
                            margin_y="15px"
                        ),
                        rx.text("No more results to show.", color="gray", padding="20px")
                    ),
                    rx.box(height="50px")
                ),
                width="100%",
            ),
            width="85%",
            flex="1"
        ),
        key=CollectionState.search_key,
        width="100%",
        height="100%",
        padding_bottom="10px",
        align_items="center"
    ),

def _search_result_card(game: dict):
    return rx.hstack(
        rx.cond(
            # Checks if an image was retrieved from IGDB and displays a placeholder if not
            game["cover_id"],
            rx.image(
                src=f"https://images.igdb.com/igdb/image/upload/t_cover_small/{game['cover_id']}.jpg",
                width="90px", 
                height="128px", 
                object_fit="contain", 
                border_radius="4px"
            ),
            rx.image(
                src="/noimg.jpg",
                width="90px",
                height="128px",
                object_fit="contain",
                border_radius="4px"
            )
        ),
        rx.vstack(
            rx.text(f"{game['title']} ({game['year']})", font_weight="bold", font_size="1.5em"),
            rx.text(f"{game['developers']}", font_size="1em", color="gray"),
            rx.text(f"{game['platforms']}", font_size="1em", color="gray"),
            align_items="start",
            spacing="0"
        ),
        rx.spacer(),
        rx.button(
            rx.cond(
                game["id"],
                rx.icon(tag="minus", size=18),
                rx.icon(tag="plus", size=18)
            ),
            on_click=lambda: CollectionState.toggle_game(game),
            color_scheme=rx.cond(game["id"], "ruby", "jade"),
            variant="soft",
            size="3",
            loading=CollectionState.is_loading
        ),
        width="100%",
        padding="10px 20px",
        border_bottom="1px solid #333",
        align_items="center",
        _hover={"bg": "rgba(255,255,255,0.05)"}
    )