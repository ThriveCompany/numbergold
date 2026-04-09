from datetime import timedelta
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from . import auth, crud, models, schemas, websocket as ws_manager
from .database import Base, engine, get_db
from .config import settings

app = FastAPI(title="Number Battle API")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post("/register", response_model=schemas.Token)
async def register(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await crud.get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    password_hash = auth.hash_password(user_data.password)
    user = await crud.create_user(db, user_data.username, password_hash)
    token = auth.create_access_token(user.id, user.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = auth.create_access_token(user.id, user.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/create", response_model=schemas.GameOut)
async def create_game(game_data: schemas.GameCreate, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    game = await crud.create_game(db, current_user.id, game_data.secret_number)
    return game


@app.post("/join", response_model=schemas.GameOut)
async def join_game(join_data: schemas.GameJoin, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    game = await crud.join_game(db, join_data.game_id, current_user.id, join_data.secret_number)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found or already joined")
    return game


@app.get("/state/{game_id}", response_model=schemas.GameOut)
async def game_state(game_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    game = await crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if current_user.id not in {game.player1_id, game.player2_id}:
        raise HTTPException(status_code=403, detail="Not a participant")
    return game


def evaluate_guess(game: models.Game, guess: int) -> Dict[str, Optional[str]]:
    if game.target_number is None:
        return {"result": None, "message": "Game has no target set."}
    if guess == game.target_number:
        return {"result": "win", "message": "Yes! You found the number."}
    if guess < game.target_number:
        return {"result": "higher", "message": "No, it\u2019s higher ⬆️"}
    return {"result": "lower", "message": "No, it\u2019s lower ⬇️"}


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: int, token: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    # Authenticate connection by JWT token in query param
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        payload = auth.jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    game = await crud.get_game_by_id(db, game_id)
    if not game or user_id not in {game.player1_id, game.player2_id}:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.manager.connect(game_id, websocket)
    try:
        await ws_manager.manager.broadcast(game_id, {
            "type": "system",
            "message": f"Player {user_id} joined the room.",
        })
        while True:
            payload = await websocket.receive_json()
            action = payload.get("action")
            if action != "guess":
                continue
            guess_value = payload.get("guess")
            if not isinstance(guess_value, int) or not 1 <= guess_value <= 100:
                await websocket.send_json({"type": "error", "message": "Guess must be a whole number from 1 to 100."})
                continue
            game = await crud.get_game_by_id(db, game_id)
            if game.status != "active":
                await websocket.send_json({"type": "error", "message": "Game is not active."})
                continue
            current_player_id = game.player1_id if game.current_turn == 1 else game.player2_id
            if user_id != current_player_id:
                await websocket.send_json({"type": "error", "message": "Wait for your turn."})
                continue
            current_player = 1 if user_id == game.player1_id else 2
            guess_result = evaluate_guess(game, guess_value)
            note = guess_result["message"]
            await crud.create_move(db, game.id, user_id, guess_value, guess_result["result"], note)
            await crud.update_game_after_guess(db, game, guess_value, guess_result["result"])
            game = await crud.get_game_by_id(db, game_id)
            broadcast_payload = {
                "type": "move",
                "game_id": game.id,
                "guess": guess_value,
                "player_id": user_id,
                "result": guess_result["result"],
                "message": note,
                "current_turn": game.current_turn,
                "min_range": game.min_range,
                "max_range": game.max_range,
                "status": game.status,
                "winner_id": game.winner_id,
            }
            await ws_manager.manager.broadcast(game_id, broadcast_payload)
    except WebSocketDisconnect:
        ws_manager.manager.disconnect(game_id, websocket)
        await ws_manager.manager.broadcast(game_id, {"type": "system", "message": "A player disconnected."})
