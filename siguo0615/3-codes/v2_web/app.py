import os
import time
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from board import Board

app = Flask(__name__, static_folder='static')

# In-memory game state
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = Board()
        self.current_player = Board.BLACK
        self.game_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_local"
        self.date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.moves_log = []  # Matches save_flie.template.json format
        self.step_count = 0
        self.winner = 0
        self.reason = "active"  # "active", "five_in_a_row", "board_full", "user_exit"
        self.last_move_time = time.time()

game_state = GameState()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/new_game', methods=['POST'])
def new_game():
    game_state.reset()
    return jsonify({
        "status": "ok",
        "game_id": game_state.game_id,
        "date": game_state.date_str,
        "board_size": Board.SIZE,
        "current_player": game_state.current_player,
        "winner": game_state.winner,
        "reason": game_state.reason,
        "moves": game_state.moves_log,
        "board": game_state.board.grid
    })

@app.route('/api/check_move', methods=['POST'])
def check_move():
    data = request.get_json() or {}
    if 'row' not in data or 'col' not in data:
        return jsonify({"status": "error", "message": "请求参数缺失"}), 400
    try:
        row = int(data['row'])
        col = int(data['col'])
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "坐标必须为整数"}), 400

    if not (0 <= row < Board.SIZE and 0 <= col < Board.SIZE):
        return jsonify({"status": "error", "message": "坐标越界"}), 400

    if game_state.board.grid[row][col] != Board.EMPTY:
        return jsonify({"status": "ok", "forbidden_type": None})

    # Only Black is checked for forbidden moves
    forbidden_type = None
    if game_state.current_player == Board.BLACK:
        forbidden_type = game_state.board.check_forbidden_move(row, col)

    return jsonify({
        "status": "ok",
        "forbidden_type": forbidden_type
    })

@app.route('/api/place', methods=['POST'])
def place_piece():
    if game_state.winner != 0 or game_state.reason != "active":
        return jsonify({
            "status": "error",
            "message": "游戏已结束，不能落子！"
        }), 400

    data = request.get_json() or {}
    
    # Payload parameter validation
    if 'row' not in data or 'col' not in data:
        return jsonify({
            "status": "error",
            "message": "请求参数缺失 row 或 col"
        }), 400

    try:
        row = int(data['row'])
        col = int(data['col'])
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "坐标必须为整数"
        }), 400

    # Boundary validation
    if not (0 <= row < Board.SIZE and 0 <= col < Board.SIZE):
        return jsonify({
            "status": "error",
            "message": f"坐标越界！坐标范围应在 0-{Board.SIZE-1} 之间"
        }), 400

    # Occupied cell validation
    if game_state.board.grid[row][col] != Board.EMPTY:
        return jsonify({
            "status": "error",
            "message": "当前位置已有棋子！"
        }), 400

    # Renju restriction validation for Black
    if game_state.current_player == Board.BLACK:
        forbidden_type = game_state.board.check_forbidden_move(row, col)
        if forbidden_type:
            return jsonify({
                "status": "error",
                "message": f"此位置触发【{forbidden_type}】，黑棋禁止落子！",
                "forbidden_type": forbidden_type
            }), 400

    # Calculate time spent for this move
    now = time.time()
    time_spent = round(now - game_state.last_move_time, 2)
    game_state.last_move_time = now

    # Execute move
    player_who_moved = game_state.current_player
    game_state.board.place_piece(row, col, player_who_moved)
    game_state.step_count += 1
    
    # Log move (using 1-based index coordinate for the pos list to match the json template format)
    game_state.moves_log.append({
        "step": game_state.step_count,
        "player": player_who_moved,
        "pos": [row + 1, col + 1],
        "time_spent": time_spent
    })

    # Check winning condition
    if game_state.board.check_winner(row, col):
        game_state.winner = player_who_moved
        game_state.reason = "five_in_a_row"
    # Check draw condition
    elif game_state.board.is_full():
        game_state.reason = "board_full"
    else:
        # Alternate turn
        game_state.current_player = Board.WHITE if game_state.current_player == Board.BLACK else Board.BLACK

    return jsonify({
        "status": "ok",
        "board": game_state.board.grid,
        "current_player": game_state.current_player,
        "winner": game_state.winner,
        "reason": game_state.reason,
        "moves": game_state.moves_log,
        "last_move": [row, col]
    })

@app.route('/api/undo', methods=['POST'])
def undo_move():
    if len(game_state.moves_log) == 0:
        return jsonify({
            "status": "error",
            "message": "无法悔棋，没有历史落子！"
        }), 400

    # In local double play, undo the last step.
    # To undo, we recreate a clean board and replay moves up to step-1
    last_move_data = game_state.moves_log.pop()
    game_state.step_count -= 1
    
    # Rebuild board state
    new_board = Board()
    for m in game_state.moves_log:
        r, c = m['pos'][0] - 1, m['pos'][1] - 1
        new_board.grid[r][c] = m['player']
        new_board.last_move = (r, c)
        
    game_state.board = new_board
    
    # Reset winner/reason status if undoing from finished game
    game_state.winner = 0
    game_state.reason = "active"
    
    # Set the current player to the player who just had their move removed
    game_state.current_player = last_move_data['player']
    game_state.last_move_time = time.time() # Reset clock

    return jsonify({
        "status": "ok",
        "board": game_state.board.grid,
        "current_player": game_state.current_player,
        "winner": game_state.winner,
        "reason": game_state.reason,
        "moves": game_state.moves_log
    })

@app.route('/api/save', methods=['GET'])
def save_game():
    save_data = {
        "game_id": game_state.game_id,
        "date": game_state.date_str,
        "players": {
            "black": "Human_Black",
            "white": "Human_White"
        },
        "board_size": Board.SIZE,
        "moves": game_state.moves_log,
        "result": {
            "winner": game_state.winner,
            "reason": game_state.reason
        }
    }
    
    # Automatically write log to 5-logs folder on server side too
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "5-logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    filepath = os.path.join(log_dir, f"game_{game_state.game_id}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass # Silently fail server-side auto-save if write issue, but return JSON

    return jsonify(save_data)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
