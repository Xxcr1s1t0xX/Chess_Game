import random
import time

import chess
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
board = chess.Board()

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}


def board_payload():
    result = None
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        result = f"Checkmate - {winner} wins"
    elif board.is_stalemate():
        result = "Draw - stalemate"
    elif board.is_insufficient_material():
        result = "Draw - insufficient material"
    elif board.is_seventyfive_moves():
        result = "Draw - seventy-five move rule"
    elif board.is_fivefold_repetition():
        result = "Draw - fivefold repetition"

    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "result": result,
        "check": board.is_check(),
        "legalMoves": sorted(move.uci() for move in board.legal_moves),
    }


def evaluate(position):
    if position.is_checkmate():
        return -1000000 if position.turn == chess.WHITE else 1000000
    if position.is_game_over():
        return 0

    score = 0
    for square, piece in position.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        center_distance = abs(3.5 - file) + abs(3.5 - rank)
        positional = -center_distance * (4 if piece.piece_type in (chess.KNIGHT, chess.BISHOP) else 2)
        score += (value + positional) if piece.color == chess.WHITE else -(value + positional)

    score += position.legal_moves.count() if position.turn == chess.WHITE else -position.legal_moves.count()
    return score


def move_order(position, move):
    score = 0
    if position.is_capture(move):
        score += 10000 + PIECE_VALUES.get(position.piece_type_at(move.to_square), 0)
    if position.gives_check(move):
        score += 5000
    if move.promotion:
        score += PIECE_VALUES[move.promotion]
    return score


def search(position, depth, alpha, beta, strength):
    if depth == 0 or position.is_game_over():
        return evaluate(position)

    moves = list(position.legal_moves)
    moves.sort(key=lambda move: move_order(position, move), reverse=True)
    if position.turn == chess.WHITE:
        value = -10000000
        for move in moves:
            position.push(move)
            value = max(value, search(position, depth - 1, alpha, beta, strength))
            position.pop()
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    value = 10000000
    for move in moves:
        position.push(move)
        value = min(value, search(position, depth - 1, alpha, beta, strength))
        position.pop()
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value


def strength_settings(level):
    level = max(300, min(3000, int(level)))
    if level < 700:
        return 1, 0.28
    if level < 1100:
        return 2, 0.18
    if level < 1500:
        return 2, 0.10
    if level < 1900:
        return 3, 0.06
    if level < 2300:
        return 4, 0.025
    if level < 2700:
        return 5, 0.01
    return 6, 0.0


def choose_move(level):
    depth, mistake_rate = strength_settings(level)
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    if random.random() < mistake_rate and len(legal_moves) > 1:
        weights = [1 + 1.5 * move_order(board, move) / 10000 for move in legal_moves]
        return random.choices(legal_moves, weights=weights, k=1)[0]

    best_move = legal_moves[0]
    best_value = -10000000 if board.turn == chess.WHITE else 10000000
    legal_moves.sort(key=lambda move: move_order(board, move), reverse=True)

    started = time.time()
    for move in legal_moves:
        board.push(move)
        value = search(board, depth - 1, -10000000, 10000000, level)
        board.pop()

        if board.turn == chess.WHITE and value > best_value:
            best_value, best_move = value, move
        elif board.turn == chess.BLACK and value < best_value:
            best_value, best_move = value, move

    return best_move


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/reset")
def reset():
    global board
    board = chess.Board()
    return jsonify(board_payload())


@app.post("/api/move")
def human_move():
    data = request.get_json(silent=True) or {}
    uci = data.get("uci", "")
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return jsonify({"error": "Invalid move format"}), 400

    if move not in board.legal_moves:
        return jsonify({"error": "Illegal move"}), 400

    board.push(move)
    return jsonify(board_payload())


@app.post("/api/ai")
def ai_move():
    data = request.get_json(silent=True) or {}
    level = data.get("level", 1500)
    move = choose_move(level)
    if move is None:
        return jsonify(board_payload())

    board.push(move)
    return jsonify({**board_payload(), "move": move.uci()})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
