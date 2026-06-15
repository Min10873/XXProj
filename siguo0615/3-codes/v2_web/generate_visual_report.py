import os
import shutil
from board import Board
from board_renderer import BoardRenderer

# Artifact directory path from metadata
ARTIFACT_DIR = "C:\\Users\\wumin\\.gemini\\antigravity-ide\\brain\\9cd27414-d3ea-4014-9a09-21d57e32248d"
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "5-logs")

def save_image(img, filename):
    # Ensure dirs exist
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if not os.path.exists(ARTIFACT_DIR):
        os.makedirs(ARTIFACT_DIR)

    # Path 1: 5-logs/
    log_path = os.path.join(LOG_DIR, filename)
    img.save(log_path)
    print(f"Saved to logs: {log_path}")

    # Path 2: Artifacts/
    art_path = os.path.join(ARTIFACT_DIR, filename)
    img.save(art_path)
    print(f"Saved to artifacts: {art_path}")

def generate_double_three():
    """Test Case 1: Double Three (三三禁手)"""
    board = Board()
    renderer = BoardRenderer()

    # Set up vertical open three
    board.grid[5][7] = Board.BLACK
    board.grid[6][7] = Board.BLACK
    
    # Set up horizontal open three
    board.grid[7][5] = Board.BLACK
    board.grid[7][6] = Board.BLACK

    # (7,7) is the double three forbidden move coordinate
    forbidden_move = (7, 7)
    forbidden_type = board.check_forbidden_move(7, 7) # Should be "三三禁手"

    # Set last move to White for background context
    board.grid[8][8] = Board.WHITE
    board.last_move = (8, 8)

    img = renderer.draw_board(
        board.grid, 
        last_move=board.last_move,
        forbidden_move=forbidden_move, 
        forbidden_type=forbidden_type
    )
    save_image(img, "test_double_three.png")

def generate_overline():
    """Test Case 2: Overline (长连禁手)"""
    board = Board()
    renderer = BoardRenderer()

    # Set up 5 black stones in a row
    for c in range(1, 6):
        board.grid[7][c] = Board.BLACK
    
    # (7,6) is the overline forbidden move coordinate
    forbidden_move = (7, 6)
    forbidden_type = "长连禁手"

    # Set last move to White
    board.grid[8][8] = Board.WHITE
    board.last_move = (8, 8)

    img = renderer.draw_board(
        board.grid, 
        last_move=board.last_move,
        forbidden_move=forbidden_move, 
        forbidden_type=forbidden_type
    )
    save_image(img, "test_overline.png")

def generate_win_five():
    """Test Case 3: Win 5 in a row (五连珠胜)"""
    board = Board()
    renderer = BoardRenderer()

    # Set up winning line horizontally: (7, 5) to (7, 9)
    winning_line = []
    for c in range(5, 10):
        board.grid[7][c] = Board.BLACK
        winning_line.append((7, c))
    
    # Add some white block stones
    board.grid[6][6] = Board.WHITE
    board.grid[8][8] = Board.WHITE

    # Last winning move is (7, 9)
    board.last_move = (7, 9)

    img = renderer.draw_board(
        board.grid, 
        last_move=board.last_move,
        winning_line=winning_line,
        winner=Board.BLACK
    )
    save_image(img, "test_win_five.png")

if __name__ == "__main__":
    print("Generating visual test screenshots...")
    generate_double_three()
    generate_overline()
    generate_win_five()
    print("Visual test generation complete!")
