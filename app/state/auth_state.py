import reflex as rx
import datetime
from logging import Logger
from sqlmodel import select
from app.models import User
from app.util import ROUTES

logger = Logger(__name__)

class AuthState(rx.State):
    user_id: int = 0
    auth_cookie: str = rx.Cookie(
        "",
        name="criticalhits_uuid",
        max_age=60 * 60 * 24 * 14,
        same_site="strict",
        path="/"
    )

    async def on_mount(self):
        """
        Called from the on_mount trigger for #main-container on the login page.
        Once logged in, redirects to the previous attempted page via ?r in the URL
        Currently a stub that sets the user to the default "local" user and redirects back to the caller.
        """
        caller_page = self.router.url.query_parameters.get("r", ROUTES['home'])
        await self.login()

        if caller_page in ROUTES.values():
            return rx.redirect(caller_page)
        else:
            return rx.redirect(ROUTES['home'])

    async def check_auth(self, caller_page: str = ROUTES['home']):
        """
        Authentication check, called from the on_mount trigger for #main-container on every non-login page.
        Redirects to login page if unauthenticated.

        Args:
            caller_page: String from util.ROUTES to pass to the login page for redirect after authentication
        """
        if self.auth_cookie:
            await self._get_user(caller_page)
        else:
            return rx.redirect(f"{ROUTES['login']}?r={caller_page}")

    async def _get_user(self, caller_page: str):
        """
        Checks the UUID contained in the user's browser cookie.
        Validation fails if user's last activity is more than 7 days ago.

        Args:
            caller_page: String from util.ROUTES to pass to the login page for redirect after authentication
        """
        try:
            async with rx.asession() as session:
                now = datetime.datetime.now(datetime.timezone.utc)
                login_expiry = now - datetime.timedelta(days=7)

                query = select(User).where(User.uuid == self.auth_cookie, User.last_activity > login_expiry)
                result = await session.exec(query)
                user = result.first()

                if user:
                    user.utc_activity = datetime.datetime.now(datetime.timezone.utc)
                    session.add(user)
                    await session.commit()
                    self.user_id = user.id
                else:
                    await self.logout(caller_page)
        except Exception as e:
            logger.error(f"[!] Database error: {e}")
            await self.logout(caller_page)

    async def login(self, auth_source: str = "local", auth_id: str = "1", display: str = "User"):
        """
        Logs the user in, creating a new account if one doesn't exist.

        Args:
            auth_source: String representing the authentication provider (e.g. Twitch)
            auth_id: String representing the unique user ID obtained from the provider
            display: User's display name as reported by the provider
        """
        async with rx.asession() as session:
            query = select(User).where(User.provider == auth_source, User.provider_id == auth_id)
            result = await session.exec(query)
            user = result.first()
            if not user:
                user = User(
                    provider=auth_source,
                    provider_id=auth_id,
                    display_name = display
                )
            else:
                user.utc_activity = datetime.datetime.now(datetime.timezone.utc)
                user.display_name = display

            session.add(user)
            await session.commit()
            await session.refresh(user)

            self.auth_cookie = user.uuid
            self.user_id = user.id

    async def logout(self, caller_page: str):
        """
        Logs the user out, removing all user data from the current session
        and clears the browser cookie. Redirects to login page.

        Args:
            caller_page: String from util.ROUTES to pass to the login page for redirect after authentication
        """
        self.user_id = 0
        self.auth_cookie = ""
        rx.remove_cookie("criticalhits_uuid")
        return rx.redirect(f"{ROUTES['login']}?r={caller_page}")