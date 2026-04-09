from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    games_as_player1 = relationship("Game", back_populates="player1", foreign_keys="Game.player1_id")
    games_as_player2 = relationship("Game", back_populates="player2", foreign_keys="Game.player2_id")
    moves = relationship("Move", back_populates="player")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    player1_secret = Column(Integer, nullable=False)
    player2_secret = Column(Integer, nullable=True)
    min_range = Column(Integer, default=1, nullable=False)
    max_range = Column(Integer, default=100, nullable=False)
    target_number = Column(Integer, nullable=True)
    current_turn = Column(Integer, default=1, nullable=False)
    status = Column(String(32), default="waiting", nullable=False)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    player1 = relationship("User", foreign_keys=[player1_id], back_populates="games_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="games_as_player2")
    moves = relationship("Move", back_populates="game", order_by="Move.timestamp")


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    guess = Column(Integer, nullable=False)
    result = Column(String(32), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    note = Column(Text, nullable=True)

    game = relationship("Game", back_populates="moves")
    player = relationship("User", back_populates="moves")
