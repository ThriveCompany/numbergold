import { BACKEND_BASE_URL } from "./config.js";

const authSection = document.getElementById("authSection");
const lobbySection = document.getElementById("lobbySection");
const gameSection = document.getElementById("gameSection");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const showLogin = document.getElementById("showLogin");
const showRegister = document.getElementById("showRegister");
const logoutBtn = document.getElementById("logoutBtn");
const createGameForm = document.getElementById("createGameForm");
const joinGameForm = document.getElementById("joinGameForm");
const guessForm = document.getElementById("guessForm");
const messages = document.getElementById("messages");
const rangeLabel = document.getElementById("rangeLabel");
const rangeBar = document.getElementById("rangeBar");
const roomIdLabel = document.getElementById("roomIdLabel");
const statusLabel = document.getElementById("statusLabel");
const turnLabel = document.getElementById("turnLabel");
const guessInput = document.getElementById("guessInput");
const toast = document.getElementById("toast");

let ws = null;
let currentGame = null;
let currentUserId = null;

function parseJwt(token) {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(decodeURIComponent(atob(payload.replace(/-/g, "+").replace(/_/g, "/")).split("").map(c => `%${(`00${c.charCodeAt(0).toString(16)}`).slice(-2)}`).join("")));
  } catch (error) {
    return null;
  }
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 3200);
}

function showSection(auth, lobby, game) {
  authSection.classList.toggle("hidden", !auth);
  lobbySection.classList.toggle("hidden", !lobby);
  gameSection.classList.toggle("hidden", !game);
}

function setActiveTab(tab) {
  showLogin.classList.toggle("active", tab === "login");
  showRegister.classList.toggle("active", tab === "register");
  loginForm.classList.toggle("hidden", tab !== "login");
  registerForm.classList.toggle("hidden", tab !== "register");
}

function getToken() {
  return localStorage.getItem("nb_token");
}

function saveToken(token) {
  localStorage.setItem("nb_token", token);
  currentUserId = parseJwt(token)?.sub;
}

function clearSession() {
  localStorage.removeItem("nb_token");
  currentUserId = null;
  if (ws) {
    ws.close();
    ws = null;
  }
}

function authorizedFetch(path, options = {}) {
  const token = getToken();
  return fetch(`${BACKEND_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : undefined,
      ...(options.headers || {}),
    },
  });
}

async function handleResponse(response) {
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? payload?.message ?? "Request failed");
  }
  return response.json();
}

function appendMessage(content, type = "system") {
  const bubble = document.createElement("div");
  bubble.className = `message ${type}`;
  bubble.innerHTML = `<span>${content}</span>`;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function updateGameUI(game) {
  currentGame = game;
  roomIdLabel.textContent = game.id;
  statusLabel.textContent = game.status;
  const currentTargetId = game.current_turn === 1 ? game.player1_id : game.player2_id;
  const turnPlayer = currentTargetId === currentUserId ? "You" : "Opponent";
  turnLabel.textContent = turnPlayer;
  rangeLabel.textContent = `Range: ${game.min_range} – ${game.max_range}`;
  const width = Math.max(2, ((game.max_range - game.min_range + 1) / 100) * 100);
  rangeBar.style.width = `${width}%`;
  guessInput.disabled = game.status === "finished";
}

async function attachWebSocket(gameId) {
  const token = getToken();
  if (!token) return;
  if (ws) {
    ws.close();
  }
  const scheme = BACKEND_BASE_URL.startsWith("https") ? "wss" : "ws";
  const url = `${scheme}://${new URL(BACKEND_BASE_URL).host}/ws/${gameId}?token=${encodeURIComponent(token)}`;
  ws = new WebSocket(url);

  ws.addEventListener("open", () => appendMessage("Connected to the room.", "system"));
  ws.addEventListener("message", event => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "system") {
        appendMessage(data.message, "system");
        return;
      }
      if (data.type === "move") {
        const owner = data.player_id === currentUserId ? "You" : "Opponent";
        appendMessage(`${owner} guessed ${data.guess}. ${data.message}`, data.player_id === currentUserId ? "user" : "system");
        updateGameUI({
          ...currentGame,
          min_range: data.min_range,
          max_range: data.max_range,
          current_turn: data.current_turn,
          status: data.status,
          winner_id: data.winner_id,
        });
        if (data.status === "finished") {
          const winner = data.winner_id === currentUserId ? "You win!" : "Opponent wins.";
          appendMessage(winner, "system");
        }
      }
    } catch (err) {
      console.error(err);
    }
  });

  ws.addEventListener("close", () => appendMessage("Realtime connection closed.", "system"));
  ws.addEventListener("error", () => appendMessage("Realtime connection error.", "system"));
}

async function loadGameState(gameId) {
  const response = await authorizedFetch(`/state/${gameId}`);
  const game = await handleResponse(response);
  updateGameUI(game);
  appendMessage(`Room ${game.id} is ready. Waiting for play.`, "system");
  return game;
}

loginForm.addEventListener("submit", async event => {
  event.preventDefault();
  try {
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;
    const response = await fetch(`${BACKEND_BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const body = await handleResponse(response);
    saveToken(body.access_token);
    showSection(false, true, false);
    showToast("Logged in successfully.");
  } catch (err) {
    showToast(err.message);
  }
});

registerForm.addEventListener("submit", async event => {
  event.preventDefault();
  try {
    const username = document.getElementById("registerUsername").value.trim();
    const password = document.getElementById("registerPassword").value;
    const response = await fetch(`${BACKEND_BASE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const body = await handleResponse(response);
    saveToken(body.access_token);
    showSection(false, true, false);
    showToast("Account created and logged in.");
  } catch (err) {
    showToast(err.message);
  }
});

showLogin.addEventListener("click", () => setActiveTab("login"));
showRegister.addEventListener("click", () => setActiveTab("register"));
logoutBtn.addEventListener("click", () => {
  clearSession();
  window.location.reload();
});

createGameForm.addEventListener("submit", async event => {
  event.preventDefault();
  const secretNumber = Number(document.getElementById("createSecret").value);
  try {
    const response = await authorizedFetch("/create", {
      method: "POST",
      body: JSON.stringify({ secret_number: secretNumber }),
    });
    const game = await handleResponse(response);
    showSection(false, false, true);
    updateGameUI(game);
    appendMessage("Game room created. Share the room ID with your opponent.", "system");
    attachWebSocket(game.id);
  } catch (err) {
    showToast(err.message);
  }
});

joinGameForm.addEventListener("submit", async event => {
  event.preventDefault();
  const gameId = Number(document.getElementById("joinGameId").value);
  const secretNumber = Number(document.getElementById("joinSecret").value);
  try {
    const response = await authorizedFetch("/join", {
      method: "POST",
      body: JSON.stringify({ game_id: gameId, secret_number: secretNumber }),
    });
    const game = await handleResponse(response);
    showSection(false, false, true);
    updateGameUI(game);
    appendMessage("Joined the room. Game is active.", "system");
    attachWebSocket(game.id);
  } catch (err) {
    showToast(err.message);
  }
});

guessForm.addEventListener("submit", async event => {
  event.preventDefault();
  const guessValue = Number(guessInput.value);
  if (!guessValue || guessValue < 1 || guessValue > 100) {
    showToast("Enter a number between 1 and 100.");
    return;
  }
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast("Realtime connection is not ready.");
    return;
  }
  ws.send(JSON.stringify({ action: "guess", guess: guessValue }));
  guessInput.value = "";
});

function initSession() {
  const token = getToken();
  if (token) {
    currentUserId = parseJwt(token)?.sub;
    showSection(false, true, false);
  } else {
    showSection(true, false, false);
  }
}

initSession();
