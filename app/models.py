import reflex as rx
from sqlmodel import SQLModel, Field, Column, text
from typing import Optional

class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    igdb_id: Optional[int] = Field(default=None, unique=True)
    igdb_cover_id: Optional[str]
    title: str
    release_year: Optional[int] = Field(default=None)
    platform: str

class ArenaChoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    winner_id: int = Field(foreign_key="game.id")
    loser_id: int = Field(foreign_key="game.id")