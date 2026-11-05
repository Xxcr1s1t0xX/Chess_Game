const PIECES = {
  w: { k: "♔", q: "♕", r: "♖", b: "♗", n: "♘", p: "♙" },
  b: { k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟" },
};

let state = null;
let mode = "ai-ai";
let running = false;
let paused = false;
let selected = null;
let moveHistory = [];
let timer = null;

const boardElement = document.getElementById("board");
const statusElement = document.getElementById("status");
const resultElement = document.getElementById("result");
const moveLogElement = document.getElementById("moveLog");

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function parseFen(fen) {
  const position = {};
  const rows = fen.split(" ")[0].split("/");
  rows.forEach((row, rankIndex) => {
    let file = 0;
    for (const char of row) {
      if (/\d/.test(char)) {
        file += Number(char);
      } else {
        position[String.fromCharCode(97 + file) + (8 - rankIndex)] = {
          color: char === char.toUpperCase() ? "w" : "b",
          type: char.toLowerCase(),
        };
        file++;
      }
    }
  });
  return position;
}

function render() {
  if (!state) return;
  const pieces = parseFen(state.fen);
  boardElement.innerHTML = "";

  for (let rank = 8; rank >= 1; rank--) {
    for (let file = 0; file < 8; file++) {
      const squareName = String.fromCharCode(97 + file) + rank;
      const square = document.createElement("button");
      square.className = "square " + ((rank + file) % 2 ? "light" : "dark");
      square.dataset.square = squareName;
      if (selected === squareName) square.classList.add("selected");
      if (lastMove().includes(squareName)) square.classList.add("last");

      if (state.legalMoves.some((move) => selected && move.startsWith(selected + squareName))) {
        square.classList.add("legal");
      }

      const piece = pieces[squareName];
      if (piece) square.textContent = PIECES[piece.color][piece.type];
      if (mode === "human-ai") {
        square.disabled = state.turn === "black" || !piece && selected !== null ? false : false;
      }
      square.addEventListener("click", () => humanSquareClick(squareName));
      boardElement.appendChild(square);
    }
  }

  const titleTurn = state.turn === "white" ? "White" : "Black";
  statusElement.textContent = state.result || `${titleTurn} to move${state.check ? " - Check!" : ""}`;
  resultElement.hidden = !state.result;
  resultElement.textContent = state.result || "";

  if (mode === "ai-ai") {
    document.getElementById("blackControls").style.display = "block";
  } else {
    document.getElementById("blackControls").style.display = "none";
  }
  updateMoveLog();
}

function lastMove() {
  return moveHistory.length ? moveHistory[moveHistory.length - 1].match(/[a-h][1-8]/g) || [] : [];
}

function updateMoveLog() {
  if (!moveHistory.length) {
    moveLogElement.textContent = "No moves yet";
    return;
  }
  const rows = [];
  for (let i = 0; i < moveHistory.length; i += 2) {
    rows.push(`${i / 2 + 1}. ${moveHistory[i]} ${moveHistory[i + 1] || ""}`);
  }
  moveLogElement.innerHTML = rows.join("<br>");
  moveLogElement.scrollTop = moveLogElement.scrollHeight;
}

async function humanSquareClick(squareName) {
  if (!state || state.result || running || mode !== "human-ai" || state.turn !== "white") return;
  const pieces = parseFen(state.fen);

  if (selected) {
    const candidates = state.legalMoves.filter((move) => move.startsWith(selected + squareName));
    if (candidates.length) {
      const promotions = candidates.filter((move) => /[qrbn]$/.test(move));
      const uci = promotions.length ? promotions.find((move) => move.endsWith("q")) || candidates[0] : candidates[0];
      try {
        state = await api("/api/move", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ uci }),
        });
        moveHistory.push(uci);
        selected = null;
        render();
        scheduleAi();
      } catch (error) {
        statusElement.textContent = error.message;
      }
      return;
    }
  }

  selected = pieces[squareName]?.color === "w" ? squareName : null;
  render();
}

async function makeAiMove() {
  if (!running || paused || !state || state.result) return;
  const turn = state.turn;
  const level = turn === "white"
    ? Number(document.getElementById("whiteLevel").value)
    : Number(document.getElementById("blackLevel").value);
  statusElement.textContent = `${turn === "white" ? "White" : "Black"} AI is thinking...`;

  try {
    const next = await api("/api/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level }),
    });
    if (next.move) moveHistory.push(next.move);
    state = next;
    render();
    scheduleNext();
  } catch (error) {
    statusElement.textContent = error.message;
  }
}

function scheduleNext() {
  if (!running || paused || !state || state.result) return;
  if (mode === "human-ai" && state.turn === "white") return;
  const delay = Number(document.getElementById("speed").value);
  timer = setTimeout(makeAiMove, delay);
}

function scheduleAi() {
  if (!running || !state || state.result || mode !== "human-ai") return;
  const delay = Number(document.getElementById("speed").value);
  timer = setTimeout(makeAiMove, delay);
}

async function reset() {
  clearTimeout(timer);
  running = false;
  paused = false;
  selected = null;
  moveHistory = [];
  state = await api("/api/reset", { method: "POST" });
  document.getElementById("startButton").disabled = false;
  document.getElementById("pauseButton").disabled = true;
  document.getElementById("pauseButton").textContent = "Pause";
  render();
}

document.querySelectorAll(".mode-button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".mode-button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    mode = button.dataset.mode;
    reset();
  });
});

["whiteLevel", "blackLevel"].forEach((id) => {
  const input = document.getElementById(id);
  input.addEventListener("input", () => {
    document.getElementById(id + "Value").textContent = input.value;
  });
});

document.getElementById("resetButton").addEventListener("click", reset);
document.getElementById("startButton").addEventListener("click", () => {
  running = true;
  paused = false;
  document.getElementById("startButton").disabled = true;
  document.getElementById("pauseButton").disabled = false;
  scheduleNext();
});
document.getElementById("pauseButton").addEventListener("click", () => {
  paused = !paused;
  document.getElementById("pauseButton").textContent = paused ? "Resume" : "Pause";
  if (!paused) scheduleNext();
});

reset();
