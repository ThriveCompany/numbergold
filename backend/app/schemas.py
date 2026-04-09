from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int
    username: str


class GameCreate(BaseModel):
    secret_number: int = Field(..., ge=1, le=100)


class GameJoin(BaseModel):
    game_id: int
    secret_number: int = Field(..., ge=1, le=100)


class MoveCreate(BaseModel):
    guess: int = Field(..., ge=1, le=100)


class MoveOut(BaseModel):
    id: int
    player_id: int
    guess: int
    result: str
    note: Optional[str] = None
    timestamp: datetime

    class Config:
        orm_mode = True


class GameOut(BaseModel):
    id: int
    player1_id: int
    player2_id: Optional[int]
    min_range: int
    max_range: int
    current_turn: int
    status: str
    winner_id: Optional[int]
    moves: List[MoveOut] = []

    class Config:
        orm_mode = True
