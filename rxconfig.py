import reflex as rx

config = rx.Config(
    app_name="Critical_Hits",
    db_url="sqlite:///data/CH-Data.db",
    async_db_url="sqlite+aiosqlite:///data/CH-Data.db",
    app_module_import="app.main",
    env_file=".env",
    plugins=[rx.plugins.RadixThemesPlugin()],
    disable_plugins=[rx.plugins.SitemapPlugin()]
)