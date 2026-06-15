import re
import time
import json
import os
from datetime import datetime
from board import Board

class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = Board.BLACK  # Black plays first
        self.cols_map_standard = "ABCDEFGHIJKLMNO"
        
        # Game recording details
        self.game_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_local"
        self.date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.moves_log = []
        self.step_count = 0

    def print_welcome(self):
        print("=" * 50)
        print("    五子棋对战平台 (Gomoku CLI) - v1 [Renju禁手版]")
        print("=" * 50)
        print("规则说明:")
        print("1. 黑棋 (●) 先手，白棋 (○) 后手。")
        print("2. 任意方向（横、竖、斜）最先连成 5 子者获胜。")
        print("3. 【禁手规则】：黑棋 ● 触发以下禁手将直接被禁止落子:")
        print("   - 长连禁手：连子数量超过 5 个")
        print("   - 三三禁手：落下一子同时形成两个或多个活三")
        print("   - 四四禁手：落下一子同时形成两个或多个四（活四/冲四）")
        print("   * 注：白棋无任何禁手限制，长连 $\ge 5$ 均可算赢。")
        print("4. 输入格式支持:")
        print("   - 字母+数字 (如: H8, h8, A1, O15)")
        print("   - 数字 空格 数字 (如: 8 8)")
        print("5. 输入 'exit' 或 'quit' 可退出游戏并自动保存棋谱。")
        print("=" * 50)

    def draw_board(self):
        """Render the board nicely in the console."""
        header = "    " + " ".join(self.cols_map_standard)
        print("\n" + header)
        
        for r in range(Board.SIZE):
            row_str = f"{r + 1:2d} "
            for c in range(Board.SIZE):
                cell = self.board.grid[r][c]
                is_last = (self.board.last_move == (r, c))
                
                if cell == Board.BLACK:
                    symbol = "●"
                elif cell == Board.WHITE:
                    symbol = "○"
                else:
                    symbol = "·"

                if is_last:
                    row_str += f"{symbol}*"
                else:
                    row_str += f"{symbol} "

            row_str += f" {r + 1:2d}"
            print(row_str)
            
        print(header + "\n")
        if self.board.last_move:
            last_r, last_c = self.board.last_move
            last_player = "黑棋 (●)" if self.board.grid[last_r][last_c] == Board.BLACK else "白棋 (○)"
            last_col_letter = self.cols_map_standard[last_c]
            print(f"提示：上一步落子位置在 {last_col_letter}{last_r + 1} ({last_player}*)\n")

    def parse_coordinate(self, user_input):
        cleaned = user_input.strip().upper()
        if not cleaned:
            return None

        # Format 1: Letter + Number (e.g. H8, H15)
        match1 = re.match(r"^([A-O])([0-9]{1,2})$", cleaned)
        if match1:
            col_letter = match1.group(1)
            row_num = int(match1.group(2))
            col_idx = self.cols_map_standard.index(col_letter)
            row_idx = row_num - 1
            return row_idx, col_idx

        # Format 2: Number + Letter (e.g. 8H)
        match2 = re.match(r"^([0-9]{1,2})([A-O])$", cleaned)
        if match2:
            row_num = int(match2.group(1))
            col_letter = match2.group(2)
            col_idx = self.cols_map_standard.index(col_letter)
            row_idx = row_num - 1
            return row_idx, col_idx

        # Format 3: Two numbers (e.g. "8 8")
        match3 = re.match(r"^([0-9]{1,2})[\s,;-]+([0-9]{1,2})$", cleaned)
        if match3:
            row_num = int(match3.group(1))
            col_num = int(match3.group(2))
            row_idx = row_num - 1
            col_idx = col_num - 1
            return row_idx, col_idx

        return None

    def save_game(self, winner, reason):
        """Export the game record to a JSON file inside the 5-logs/ directory."""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "5-logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        save_data = {
            "game_id": self.game_id,
            "date": self.date_str,
            "players": {
                "black": "Human_Black",
                "white": "Human_White"
            },
            "board_size": Board.SIZE,
            "moves": self.moves_log,
            "result": {
                "winner": winner,
                "reason": reason
            }
        }
        
        filepath = os.path.join(log_dir, f"game_{self.game_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            print(f"\n【系统提示】棋谱已成功保存至：{filepath}")
        except Exception as e:
            print(f"\n【系统提示】保存棋谱失败: {e}")

    def start(self):
        """Start the game loop."""
        self.print_welcome()
        winner = 0
        reason = "draw"
        
        while True:
            self.draw_board()
            player_symbol = "● (黑棋)" if self.current_player == Board.BLACK else "○ (白棋)"
            
            try:
                start_time = time.time()
                user_input = input(f"轮到 [{player_symbol}] 落子，请输入坐标 (例如 H8): ")
                time_spent = round(time.time() - start_time, 2)
                
                # Check for exit commands
                if user_input.strip().lower() in ['exit', 'quit']:
                    print("游戏已退出。正在保存棋谱...")
                    reason = "user_exit"
                    break
                
                coords = self.parse_coordinate(user_input)
                if coords is None:
                    print("错误：无效的输入格式！请输入合法的坐标，例如 'H8' 或 '8 8'。")
                    continue
                
                row, col = coords
                if not (0 <= row < Board.SIZE and 0 <= col < Board.SIZE):
                    print(f"错误：坐标越界！行需在 1-15 之间，列需在 A-O 之间。")
                    continue
                
                # Check occupancy
                if self.board.grid[row][col] != Board.EMPTY:
                    print("错误：该位置已经有棋子，请选择其他位置！")
                    continue
                
                # Check Renju restrictions for Black
                if self.current_player == Board.BLACK:
                    forbidden_type = self.board.check_forbidden_move(row, col)
                    if forbidden_type:
                        print(f"错误：此位置触发【{forbidden_type}】，黑棋禁止落子，请重新选择！")
                        continue
                
                # Place piece
                self.board.place_piece(row, col, self.current_player)
                self.step_count += 1
                
                # Record move (1-indexed row and col for natural output)
                self.moves_log.append({
                    "step": self.step_count,
                    "player": self.current_player,
                    "pos": [row + 1, col + 1],
                    "time_spent": time_spent
                })
                
                # Check win condition
                if self.board.check_winner(row, col):
                    self.draw_board()
                    winner = self.current_player
                    winner_name = "黑棋 (●)" if self.current_player == Board.BLACK else "白棋 (○)"
                    reason = "five_in_a_row"
                    print("=" * 50)
                    print(f"恭喜！{winner_name} 胜出，游戏结束！")
                    print("=" * 50)
                    break
                
                # Check draw condition
                if self.board.is_full():
                    self.draw_board()
                    reason = "board_full"
                    print("=" * 50)
                    print("棋盘已满，双方平局！")
                    print("=" * 50)
                    break
                
                # Alternate player
                self.current_player = Board.WHITE if self.current_player == Board.BLACK else Board.BLACK
                
            except (KeyboardInterrupt, SystemExit):
                print("\n检测到中断，游戏已退出并自动保存棋谱。")
                reason = "user_interrupt"
                break
            except Exception as e:
                print(f"发生未知错误: {e}，请重新输入。")
                
        # Save game state at the end
        self.save_game(winner, reason)
