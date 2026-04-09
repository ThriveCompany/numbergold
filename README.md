# Number Battle

Number Battle is a real-time multiplayer guessing game built with FastAPI, PostgreSQL, and a modern dark-themed frontend.

Players create or join a room, pick a secret number, and take turns asking "Is your number X?" while the UI tracks the current range and history.

## Project Structure

- `backend/` - FastAPI server, JWT auth, SQLAlchemy models, WebSocket gameplay
- `frontend/` - Vanilla HTML/CSS/JS single-page client
- `tests/` - Example test cases

## Backend Setup

### Requirements

- Python 3.11+
- PostgreSQL / Supabase database
- `pip` installed

### Install dependencies

```bash
cd backend
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### Environment

Copy `.env.example` to `.env` and update values:

```bash
cp backend/.env.example backend/.env
```

Example variables:

```env
DATABASE_URL=postgresql+asyncpg://username:password@db-host:5432/numberbattle
JWT_SECRET_KEY=replace-with-a-strong-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BACKEND_URL=http://localhost:8000
```

### Run locally

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will auto-create the database schema on startup.

## Frontend Setup

The frontend is a static single-page app.

Open `frontend/index.html` in a browser, or serve the folder from a static server.

If the backend is not at `http://localhost:8000`, update `frontend/config.js`:

```js
export const BACKEND_BASE_URL = "https://your-backend-url.example";
```

## Running Tests

From the repository root:

```bash
cd backend
pytest ../tests/test_auth.py
```

## Deploying Backend

### Render

1. Create a new Web Service.
2. Connect your repository.
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Set environment variables from `.env.example`.
6. Use a Supabase PostgreSQL database for `DATABASE_URL`.

### Railway

1. Create a new service and choose Python.
2. Add the same env vars from `.env.example`.
3. Deploy using `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## Deploying Frontend

### Vercel

1. Create a new Vercel project pointing at this repo.
2. Set `public` as the root if you deploy only static files.
3. Make sure `frontend/config.js` points to the deployed backend URL.

### GitHub Pages

1. Publish the `frontend/` folder as a static site.
2. Ensure `config.js` uses the backend URL.

## Gameplay Flow

1. Register or login.
2. Create a room and choose a secret number.
3. Share the game ID with your opponent.
4. Opponent joins with their own secret number.
5. Players take turns guessing until one player gets a "Yes".

## Database Schema

- `users`: id, username, password_hash, created_at
- `games`: id, player1_id, player2_id, player1_secret, player2_secret, min_range, max_range, target_number, current_turn, status, winner_id
- `moves`: id, game_id, player_id, guess, result, timestamp, note

## Notes

- The WebSocket endpoint is at `/ws/{game_id}` and requires the JWT token as a query parameter.
- The frontend uses a chat-style UI to show guesses and system responses.
- Use environment variables for all secrets in production.
