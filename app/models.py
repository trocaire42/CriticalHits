import reflex as rx
from sqlmodel import SQLModel, Field

class Game(SQLModel, table=True):
    id: int = Field(primary_key=True)  # RAWG ID
    title: str
    release_year: int
    platform: str
    cover_url: str