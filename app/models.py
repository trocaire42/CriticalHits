from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, CheckConstraint
from sqlalchemy import event, text
import uuid
import datetime

class Collection(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="user.id", ondelete="CASCADE")
    game_id: int = Field(primary_key=True, foreign_key="game.id", ondelete="CASCADE")

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    provider: str
    provider_id: str
    display_name: str
    last_activity: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    collection: list["Game"] = Relationship(back_populates="users", link_model=Collection)
    choices: list["ArenaChoice"] = Relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint("provider_id", "provider", name="unique_user"),
    )

    @property
    def utc_activity(self) -> datetime.datetime:
        """
        Returns the user's last_activity timestamp as a timezone-aware object in UTC
        """
        if self.last_activity.tzinfo is None:
            return self.last_activity.replace(tzinfo=datetime.timezone.utc)
        return self.last_activity

    @utc_activity.setter
    def utc_activity(self, value: datetime.datetime):
        """
        Ensures any datetime value is converted to UTC before storing
        """
        if value.tzinfo is None:
            self.last_activity = value.replace(tzinfo=datetime.timezone.utc)
        else:
            self.last_activity = value.astimezone(datetime.timezone.utc)

class Game(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    igdb_id: int | None = Field(default=None, unique=True)
    igdb_cover_id: str | None
    title: str
    release_year: int | None = Field(default=None)
    platforms: str | None = Field(default=None)
    developers: str | None = Field(default=None)

    users: list["User"] = Relationship(back_populates="collection", link_model=Collection)

class ArenaChoice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    game_a_id: int = Field(foreign_key="game.id", ondelete="CASCADE") # Lower ID in the pair, for use in the constraint
    game_b_id: int = Field(foreign_key="game.id", ondelete="CASCADE") # Higher ID in the pair
    winner_id: int = Field(foreign_key="game.id", ondelete="CASCADE", index=True) # will match either game_a_id or game_b_id
    loser_id: int = Field(foreign_key="game.id", ondelete="CASCADE", index=True) # will match either game_a_id or game_b_id

    user: "User" = Relationship(back_populates="choices")

    __table_args__ = (
        UniqueConstraint("user_id", "game_a_id", "game_b_id", name="unique_pair"),
        CheckConstraint(
            "(game_a_id < game_b_id) " \
            "AND (winner_id IN (game_a_id, game_b_id)) " \
            "AND (loser_id IN (game_a_id, game_b_id)) " \
            "AND (winner_id != loser_id)",
            name="valid_pair"
        )
    )

def update_timestamp(connection, user_id):
    """
    Helper function to update the user's last_activity timestamp.
    Called via collection_listener() or arena_listener() whenever the
    user's collection or arena choices are modified.

    Args:
        connection: Database connection to use for the update
        user_id: Integer ID for the user to update
    """
    if user_id:
        connection.execute(
            text("UPDATE user SET last_activity = :now WHERE id = :uid"),
            {"now": datetime.datetime.now(datetime.timezone.utc), "uid": user_id}
        )

@event.listens_for(Collection, "after_insert")
@event.listens_for(Collection, "after_delete")
def collection_listener(_, connection, target):
    update_timestamp(connection, target.user_id)

@event.listens_for(ArenaChoice, "after_insert")
@event.listens_for(ArenaChoice, "after_delete")
def arena_listener(_, connection, target):
    update_timestamp(connection, target.user_id)