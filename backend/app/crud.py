from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from . import models


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.username == username))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, username: str, password_hash: str) -> models.User:
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_game(db: AsyncSession, player1_id: int, secret_number: int) -> models.Game:
    game = models.Game(
        player1_id=player1_id,
        player1_secret=secret_number,
        min_range=1,
        max_range=100,
        status="waiting",
        current_turn=1,
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game


async def join_game(db: AsyncSession, game_id: int, player2_id: int, secret_number: int) -> Optional[models.Game]:
    game = await get_game_by_id(db, game_id)
    if not game or game.player2_id is not None or game.status != "waiting":
        return None
    game.player2_id = player2_id
    game.player2_secret = secret_number
    game.target_number = secret_number
    game.min_range = 1
    game.max_range = 100
    game.status = "active"
    game.current_turn = 1
    await db.commit()
    await db.refresh(game)
    return game


async def get_game_by_id(db: AsyncSession, game_id: int) -> Optional[models.Game]:
    result = await db.execute(select(models.Game).where(models.Game.id == game_id))
    return result.scalars().first()


async def create_move(db: AsyncSession, game_id: int, player_id: int, guess: int, result: str, note: Optional[str]) -> models.Move:
    move = models.Move(game_id=game_id, player_id=player_id, guess=guess, result=result, note=note)
    db.add(move)
    await db.commit()
    await db.refresh(move)
    return move


async def update_game_after_guess(db: AsyncSession, game: models.Game, guess: int, result: str) -> models.Game:
    if result == "higher":
        game.min_range = max(game.min_range, guess + 1)
        game.current_turn = 2 if game.current_turn == 1 else 1
    elif result == "lower":
        game.max_range = min(game.max_range, guess - 1)
        game.current_turn = 2 if game.current_turn == 1 else 1
    elif result == "win":
        game.status = "finished"
        # winner is current guesser
        game.winner_id = game.player1_id if game.current_turn == 1 else game.player2_id
    if game.status != "finished" and game.current_turn == 1:
        game.target_number = game.player2_secret
        game.min_range = 1
        game.max_range = 100
    elif game.status != "finished" and game.current_turn == 2:
        game.target_number = game.player1_secret
        game.min_range = 1
        game.max_range = 100
    await db.commit()
    await db.refresh(game)
    return game
