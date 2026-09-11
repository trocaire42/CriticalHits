import reflex as rx

config = rx.Config(
    app_name="gamerank",
    db_url="sqlite:///data/gamerank.db",
    async_db_url="sqlite+aiosqlite:///data/gamerank.db",
    app_module_import="app.main",
    env_file=".env",
    plugins=[rx.plugins.RadixThemesPlugin()],
    disable_plugins=[rx.plugins.SitemapPlugin()]
)