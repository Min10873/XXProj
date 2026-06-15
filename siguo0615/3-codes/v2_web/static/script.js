// Game constants
const SIZE = 15;
const CELL_COUNT = 14;
const PADDING = 30;
const BLACK = 1;
const WHITE = 2;
const EMPTY = 0;

// Coordinates standard map
const COLS_MAP = "ABCDEFGHIJKLMNO";

// State variables
let board = Array(SIZE).fill().map(() => Array(SIZE).fill(EMPTY));
let currentPlayer = BLACK;
let winner = 0;
let reason = "active";
let stepCount = 0;
let lastMove = null;
let hoverCoord = null;
let hoverForbiddenType = null;
let lastHoverCheck = { row: -1, col: -1 };

// Canvas setup
const canvas = document.getElementById("board-canvas");
const ctx = canvas.getContext("2d");
const width = canvas.width;
const height = canvas.height;
const gridSpacing = (width - 2 * PADDING) / CELL_COUNT;

// Elements
const statusBadge = document.getElementById("status-badge");
const playerBlackBox = document.getElementById("player-black-box");
const playerWhiteBox = document.getElementById("player-white-box");
const statSteps = document.getElementById("stat-steps");
const statTime = document.getElementById("stat-time");
const btnRestart = document.getElementById("btn-restart");
const btnUndo = document.getElementById("btn-undo");
const btnSave = document.getElementById("btn-save");
const moveHistoryList = document.getElementById("move-history-list");

// Modal Elements
const alertModal = document.getElementById("alert-modal");
const modalTitle = document.getElementById("modal-title");
const modalMessage = document.getElementById("modal-message");
const modalBtnOk = document.getElementById("modal-btn-ok");

// Timer variables
let turnStartTime = Date.now();
let timerInterval = null;

// Initialize
window.onload = () => {
    initCoords();
    newGame();
    setupEventListeners();
    startTimer();
};

// Start step timer
function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    turnStartTime = Date.now();
    timerInterval = setInterval(() => {
        if (winner === 0 && reason === "active") {
            const spent = ((Date.now() - turnStartTime) / 1000).toFixed(1);
            statTime.textContent = `${spent}s`;
        }
    }, 100);
}

// Draw Coordinates labels in DOM
function initCoords() {
    const topCoord = document.querySelector(".top-coord");
    const bottomCoord = document.querySelector(".bottom-coord");
    const leftCoord = document.querySelector(".left-coord");
    const rightCoord = document.querySelector(".right-coord");

    topCoord.innerHTML = "";
    bottomCoord.innerHTML = "";
    leftCoord.innerHTML = "";
    rightCoord.innerHTML = "";

    // Cols: A-O
    for (let c = 0; c < SIZE; c++) {
        const char = COLS_MAP[c];
        topCoord.innerHTML += `<div style="flex: 1; text-align: center;">${char}</div>`;
        bottomCoord.innerHTML += `<div style="flex: 1; text-align: center;">${char}</div>`;
    }

    // Rows: 1-15
    for (let r = 0; r < SIZE; r++) {
        const num = r + 1;
        leftCoord.innerHTML += `<div style="height: ${gridSpacing}px; display: flex; align-items: center; justify-content: center;">${num}</div>`;
        rightCoord.innerHTML += `<div style="height: ${gridSpacing}px; display: flex; align-items: center; justify-content: center;">${num}</div>`;
    }
}

// Call API to initialize game
async function newGame() {
    try {
        const response = await fetch("/api/new_game", { method: "POST" });
        const data = await response.json();
        updateGameState(data);
        showDialog("五子棋新局已开始", "黑棋先手落子。黑棋受禁手规则（三三、四四、长连）限制，白棋无限制。");
    } catch (err) {
        console.error("Error creating new game:", err);
    }
}

// Event Listeners
function setupEventListeners() {
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseleave", onMouseLeave);
    canvas.addEventListener("click", onBoardClick);
    
    btnRestart.addEventListener("click", newGame);
    btnUndo.addEventListener("click", undoMove);
    btnSave.addEventListener("click", saveGame);
    
    modalBtnOk.addEventListener("click", () => {
        alertModal.classList.remove("active");
    });
}

// Update game variables and UI elements
function updateGameState(data) {
    if (data.status === "ok") {
        board = data.board;
        currentPlayer = data.current_player;
        winner = data.winner;
        reason = data.reason;
        stepCount = data.moves ? data.moves.length : 0;
        lastMove = data.last_move || (data.moves && data.moves.length > 0 ? [data.moves[data.moves.length-1].pos[0]-1, data.moves[data.moves.length-1].pos[1]-1] : null);
        
        // Update stats
        statSteps.textContent = stepCount;
        
        // Turn UI Indicators
        if (winner !== 0) {
            statusBadge.textContent = "对局结束";
            statusBadge.classList.add("game-over");
            playerBlackBox.classList.remove("active");
            playerWhiteBox.classList.remove("active");
            
            const winnerName = winner === BLACK ? "黑棋 (●)" : "白棋 (○)";
            showDialog("对局结束", `恭喜！${winnerName} 连子成五，取得胜利！`);
        } else if (reason === "board_full") {
            statusBadge.textContent = "平局";
            statusBadge.classList.add("game-over");
            showDialog("对局结束", "棋盘已满，双方和棋！");
        } else {
            statusBadge.textContent = "对局进行中";
            statusBadge.classList.remove("game-over");
            
            if (currentPlayer === BLACK) {
                playerBlackBox.classList.add("active");
                playerWhiteBox.classList.remove("active");
            } else {
                playerWhiteBox.classList.add("active");
                playerBlackBox.classList.remove("active");
            }
        }

        // Render Moves Log
        renderMovesHistory(data.moves || []);
        
        // Redraw Canvas
        drawBoard();
        startTimer();
    }
}

// Render Move History List
function renderMovesHistory(moves) {
    moveHistoryList.innerHTML = "";
    if (moves.length === 0) {
        moveHistoryList.innerHTML = `<div class="empty-history-text">暂无落子记录</div>`;
        return;
    }

    moves.forEach(m => {
        const playerDotClass = m.player === BLACK ? "black" : "white";
        const playerText = m.player === BLACK ? "黑子" : "白子";
        const colLetter = COLS_MAP[m.pos[1] - 1];
        const rowNum = m.pos[0];
        
        const item = document.createElement("div");
        item.className = "move-log-item";
        item.innerHTML = `
            <span class="step">#${m.step}</span>
            <span class="player-indicator">
                <span class="player-dot ${playerDotClass}"></span>
                ${playerText}
            </span>
            <span class="pos">${colLetter}${rowNum}</span>
            <span class="time">${m.time_spent}s</span>
        `;
        moveHistoryList.appendChild(item);
    });
    // Auto scroll to bottom
    moveHistoryList.scrollTop = moveHistoryList.scrollHeight;
}

// Undo API Call
async function undoMove() {
    try {
        const response = await fetch("/api/undo", { method: "POST" });
        if (response.status === 400) {
            const err = await response.json();
            showDialog("悔棋失败", err.message);
            return;
        }
        const data = await response.json();
        updateGameState(data);
    } catch (err) {
        console.error("Error undoing move:", err);
    }
}

// Save game JSON
async function saveGame() {
    try {
        const response = await fetch("/api/save");
        const data = await response.json();
        
        // Trigger browser file download
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(jsonPrettyPrint(data));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `gomoku_game_${data.game_id}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
        
        showDialog("保存成功", "对局 JSON 棋谱已下载，并同时自动同步备份在后端的 5-logs 文件夹中。");
    } catch (err) {
        console.error("Error saving game:", err);
    }
}

function jsonPrettyPrint(obj) {
    return JSON.stringify(obj, null, 4);
}

// Show alert modal
function showDialog(title, message) {
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    alertModal.classList.add("active");
}

// Mouse Move: hover coordinates calculation and check forbidden moves
async function onMouseMove(e) {
    if (winner !== 0 || reason !== "active") return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Get closest grid coordinates
    const col = Math.round((x - PADDING) / gridSpacing);
    const row = Math.round((y - PADDING) / gridSpacing);

    if (col >= 0 && col < SIZE && row >= 0 && row < SIZE) {
        if (board[row][col] === EMPTY) {
            // Check if coordinates changed to avoid spamming
            if (lastHoverCheck.row !== row || lastHoverCheck.col !== col) {
                lastHoverCheck = { row, col };
                hoverCoord = { row, col };
                hoverForbiddenType = null;
                
                // If it is BLACK's turn, call backend to check if this is a forbidden move
                if (currentPlayer === BLACK) {
                    try {
                        const response = await fetch("/api/check_move", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ row, col })
                        });
                        const res = await response.json();
                        if (res.forbidden_type) {
                            hoverForbiddenType = res.forbidden_type;
                        }
                    } catch (err) {
                        // Suppress error
                    }
                }
                drawBoard();
            }
        } else {
            clearHover();
        }
    } else {
        clearHover();
    }
}

function onMouseLeave() {
    clearHover();
}

function clearHover() {
    hoverCoord = null;
    hoverForbiddenType = null;
    lastHoverCheck = { row: -1, col: -1 };
    drawBoard();
}

// On Click Board
async function onBoardClick(e) {
    if (winner !== 0 || reason !== "active") return;
    if (!hoverCoord) return;

    try {
        const response = await fetch("/api/place", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ row: hoverCoord.row, col: hoverCoord.col })
        });
        
        if (response.status === 400) {
            const err = await response.json();
            showDialog("落子无效", err.message);
            clearHover();
            return;
        }

        const data = await response.json();
        updateGameState(data);
        clearHover();
    } catch (err) {
        console.error("Error placing piece:", err);
    }
}

// Main Draw Canvas Board function
function drawBoard() {
    ctx.clearRect(0, 0, width, height);

    // Draw Grid board background (translucent styling)
    ctx.fillStyle = "rgba(255, 255, 255, 0.02)";
    ctx.fillRect(0, 0, width, height);

    // Grid lines styling
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1.2;

    // Draw grid lines
    for (let i = 0; i < SIZE; i++) {
        // Horizontal line
        ctx.beginPath();
        ctx.moveTo(PADDING, PADDING + i * gridSpacing);
        ctx.lineTo(width - PADDING, PADDING + i * gridSpacing);
        ctx.stroke();

        // Vertical line
        ctx.beginPath();
        ctx.moveTo(PADDING + i * gridSpacing, PADDING);
        ctx.lineTo(PADDING + i * gridSpacing, height - PADDING);
        ctx.stroke();
    }

    // Draw Star points (星位)
    const stars = [
        { r: 3, c: 3 }, { r: 3, c: 11 },
        { r: 7, c: 7 },
        { r: 11, c: 3 }, { r: 11, c: 11 }
    ];
    ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
    stars.forEach(star => {
        ctx.beginPath();
        ctx.arc(PADDING + star.c * gridSpacing, PADDING + star.r * gridSpacing, 4, 0, Math.PI * 2);
        ctx.fill();
    });

    // Draw Pieces
    for (let r = 0; r < SIZE; r++) {
        for (let c = 0; c < SIZE; c++) {
            const cell = board[r][c];
            if (cell !== EMPTY) {
                drawPiece(r, c, cell, lastMove && lastMove[0] === r && lastMove[1] === c);
            }
        }
    }

    // Draw Hover Preview
    if (hoverCoord && board[hoverCoord.row][hoverCoord.col] === EMPTY) {
        if (hoverForbiddenType) {
            // Draw Forbidden warning preview: Red dotted preview
            drawHoverPreview(hoverCoord.row, hoverCoord.col, "rgba(253, 56, 127, 0.45)", true);
        } else {
            // Draw normal preview
            const previewColor = currentPlayer === BLACK ? "rgba(0, 0, 0, 0.4)" : "rgba(255, 255, 255, 0.4)";
            drawHoverPreview(hoverCoord.row, hoverCoord.col, previewColor, false);
        }
    }
}

// Draw single piece with radial gradient and shadow
function drawPiece(row, col, player, isLast) {
    const x = PADDING + col * gridSpacing;
    const y = PADDING + row * gridSpacing;
    const radius = gridSpacing * 0.42;

    ctx.save();
    
    // Shadow
    ctx.shadowColor = "rgba(0, 0, 0, 0.45)";
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 4;

    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);

    // Gradients
    let grad;
    if (player === BLACK) {
        grad = ctx.createRadialGradient(x - radius/3, y - radius/3, 1, x, y, radius);
        grad.addColorStop(0, "#555");
        grad.addColorStop(0.2, "#2c2c2c");
        grad.addColorStop(0.8, "#0d0d0d");
        grad.addColorStop(1, "#050505");
        ctx.fillStyle = grad;
        ctx.fill();
        
        // Edge highlighting
        ctx.shadowColor = 'transparent';
        ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
        ctx.lineWidth = 1;
        ctx.stroke();
    } else {
        grad = ctx.createRadialGradient(x - radius/3, y - radius/3, 1, x, y, radius);
        grad.addColorStop(0, "#ffffff");
        grad.addColorStop(0.2, "#f2f2f2");
        grad.addColorStop(0.85, "#dfdfdf");
        grad.addColorStop(1, "#c0c0c0");
        ctx.fillStyle = grad;
        ctx.fill();
        
        ctx.shadowColor = 'transparent';
        ctx.strokeStyle = "rgba(0, 0, 0, 0.15)";
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    // Last Move Highlight Glow indicator
    if (isLast) {
        ctx.shadowColor = 'transparent';
        ctx.beginPath();
        ctx.arc(x, y, radius + 4, 0, Math.PI * 2);
        ctx.strokeStyle = player === BLACK ? "rgba(0, 242, 254, 0.6)" : "rgba(253, 56, 127, 0.6)";
        ctx.lineWidth = 2.5;
        ctx.stroke();
    }

    ctx.restore();
}

// Draw Hover Preview and optional Warn Text
function drawHoverPreview(row, col, color, isForbidden) {
    const x = PADDING + col * gridSpacing;
    const y = PADDING + row * gridSpacing;
    const radius = gridSpacing * 0.42;

    ctx.save();
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();

    if (isForbidden) {
        // Red dashed outer circle
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = "rgba(253, 56, 127, 0.9)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, radius + 2, 0, Math.PI * 2);
        ctx.stroke();

        // Draw warning text "禁" on preview stone
        ctx.fillStyle = "#fff";
        ctx.font = "bold 12px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("禁", x, y);

        // Tooltip text box above the cell
        const tooltipText = `⚠️ 黑棋: ${hoverForbiddenType}`;
        ctx.font = "500 11px Inter, sans-serif";
        const textWidth = ctx.measureText(tooltipText).width;
        
        ctx.fillStyle = "rgba(253, 56, 127, 0.95)";
        ctx.beginPath();
        roundRect(ctx, x - textWidth/2 - 8, y - radius - 26, textWidth + 16, 20, 6);
        ctx.fill();

        ctx.fillStyle = "#fff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(tooltipText, x, y - radius - 16);
    } else {
        // Normal outer border
        ctx.strokeStyle = currentPlayer === BLACK ? "rgba(255,255,255,0.2)" : "rgba(0,0,0,0.2)";
        ctx.lineWidth = 1;
        ctx.stroke();
    }
    ctx.restore();
}

// Helper to draw rounded rect
function roundRect(ctx, x, y, width, height, radius) {
    if (typeof radius === 'undefined') {
        radius = 5;
    }
    if (typeof radius === 'number') {
        radius = {tl: radius, tr: radius, br: radius, bl: radius};
    } else {
        var defaultRadius = {tl: 0, tr: 0, br: 0, bl: 0};
        for (var side in defaultRadius) {
            radius[side] = radius[side] || defaultRadius[side];
        }
    }
    ctx.beginPath();
    ctx.moveTo(x + radius.tl, y);
    ctx.lineTo(x + width - radius.tr, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);
    ctx.lineTo(x + width, y + height - radius.br);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);
    ctx.lineTo(x + radius.bl, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);
    ctx.lineTo(x, y + radius.tl);
    ctx.quadraticCurveTo(x, y, x + radius.tl, y);
    ctx.closePath();
}
