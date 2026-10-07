import reflex as rx
from typing import Any
from app.state.collection_state import CollectionState

def search_pane():
    return rx.vstack(
        # Search Form
        rx.form(
            rx.hstack(
                rx.input(
                    placeholder="Search for a game...",
                    on_change=CollectionState.set_search_query,
                    class_name="search-input search-input-text"
                ),
                rx.button(
                    rx.icon(tag="search", size=14),
                    type="submit",
                    variant="outline",
                    color_scheme="blue",
                    size="3",
                    disabled=CollectionState.search_query.length() < 3,
                    loading=CollectionState.is_loading
                ),
                class_name="search-form"
            ),
            on_submit=CollectionState.search_new
        ),
        rx.text(
            "Search results powered by ",
            rx.link(
                "IGDB",
                href="https://www.igdb.com",
                target="_blank",
                class_name="link-default"
            ),
            class_name="search-api-attrib"
        ),
        rx.divider(width="100%"),
    
        # Results Section
        rx.scroll_area(
            rx.vstack(
                rx.cond(
                    CollectionState.search_key > 0,
                    rx.foreach(CollectionState.search_results, _search_result_card),
                    rx.vstack(
                        rx.icon(tag="search", size=40),
                        rx.text("Search for a game to build your collection"),
                        align="center",
                        spacing="2",
                        class_name="search-info"
                    )
                ),
                align="center",
                spacing="0"
            ),
            rx.box(
                rx.cond(
                    CollectionState.search_key > 0,
                    rx.cond(
                        CollectionState.search_more,
                        rx.button(
                            "Load More",
                            variant="outline",
                            color_scheme="blue",
                            size="4",
                            on_click=CollectionState.search_continue,
                            loading=CollectionState.is_loading,
                            class_name="button-default-text"
                        ),
                        rx.text("No more results to show.", class_name="search-info")
                    )
                ),
                class_name="search-footer"
            ),
            key=CollectionState.search_key,
            class_name="search-results-pane"
        ),
        id="center-pane"
    ),

def _search_result_card(game: dict[str, Any]):
    return rx.hstack(
        # Checks if an image was retrieved from IGDB and displays a placeholder if not
        rx.image(
            src=rx.cond(
                game.get("cover_id"),
                f"https://images.igdb.com/igdb/image/upload/t_cover_small/{game['cover_id']}.jpg",
                "/images/noimg.jpg"
            ),
            class_name="search-results-img"
        ),
        rx.vstack(
            rx.text(f"{game['title']}", class_name="search-results-title"),
            rx.text(f"{game['year']}", class_name="search-results-year"),
            rx.text(f"{game['developers']}", class_name="search-results-info"),
            rx.text(f"{game['platforms']}", class_name="search-results-info"),
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
        class_name="search-results-card"
    )