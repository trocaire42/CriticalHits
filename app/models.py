import reflex as rx
from sqlmodel import SQLModel, Field, Column, text
from typing import Optional

class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rawg_id: Optional[int] = Field(default=None, unique=True)
    title: str
    release_year: int
    platform: str
    cover_url: str