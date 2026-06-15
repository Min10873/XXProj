import unittest
from board import Board

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_initial_board_is_empty(self):
        """Verify the board is empty upon initialization."""
        for r in range(Board.SIZE):
            for c in range(Board.SIZE):
                self.assertEqual(self.board.grid[r][c], Board.EMPTY)

    def test_place_piece_valid(self):
        """Test placing a piece in a valid empty spot."""
        success = self.board.place_piece(7, 7, Board.BLACK)
        self.assertTrue(success)
        self.assertEqual(self.board.grid[7][7], Board.BLACK)
        self.assertEqual(self.board.last_move, (7, 7))

    def test_place_piece_invalid_occupied(self):
        """Test placing a piece on an already occupied spot."""
        self.board.place_piece(7, 7, Board.BLACK)
        success = self.board.place_piece(7, 7, Board.WHITE)
        self.assertFalse(success)
        self.assertEqual(self.board.grid[7][7], Board.BLACK)

    def test_place_piece_out_of_bounds(self):
        """Test placing a piece outside boundaries."""
        self.assertFalse(self.board.is_valid_move(-1, 0))
        self.assertFalse(self.board.is_valid_move(15, 0))

    # --- Renju Restrictions (Black) ---

    def test_black_overline_restriction(self):
        """Test that Black is forbidden from creating an overline (6+ stones)."""
        # Set up 5 black stones: (7, 1) to (7, 5)
        for c in range(1, 6):
            self.board.grid[7][c] = Board.BLACK
        
        # Placing at (7, 6) would make it 6 in a row (overline)
        is_forbidden = self.board.check_forbidden_move(7, 6)
        self.assertEqual(is_forbidden, "长连禁手")
        
        # Placing at (7, 6) should fail for Black
        success = self.board.place_piece(7, 6, Board.BLACK)
        self.assertFalse(success)

    def test_black_double_three_restriction(self):
        """Test that Black is forbidden from creating double threes (三三禁手)."""
        # Create first open three vertically: e.g. (5, 7) and (6, 7). Placing at (7, 7) would make it a vertical three.
        # Open three: empty space on both sides.
        self.board.grid[5][7] = Board.BLACK
        self.board.grid[6][7] = Board.BLACK
        # Create second open three horizontally: (7, 5) and (7, 6). Placing at (7, 7) makes a horizontal three.
        self.board.grid[7][5] = Board.BLACK
        self.board.grid[7][6] = Board.BLACK

        # (7, 7) should be a double three (三三禁手)
        is_forbidden = self.board.check_forbidden_move(7, 7)
        self.assertEqual(is_forbidden, "三三禁手")
        
        success = self.board.place_piece(7, 7, Board.BLACK)
        self.assertFalse(success)

    def test_black_double_four_restriction(self):
        """Test that Black is forbidden from creating double fours (四四禁手)."""
        # Vertical four: (4, 7), (5, 7), (6, 7). Placing at (7, 7) makes a four.
        self.board.grid[4][7] = Board.BLACK
        self.board.grid[5][7] = Board.BLACK
        self.board.grid[6][7] = Board.BLACK
        # Horizontal four: (7, 4), (7, 5), (7, 6). Placing at (7, 7) makes a four.
        self.board.grid[7][4] = Board.BLACK
        self.board.grid[7][5] = Board.BLACK
        self.board.grid[7][6] = Board.BLACK

        # (7, 7) should be a double four (四四禁手)
        is_forbidden = self.board.check_forbidden_move(7, 7)
        self.assertEqual(is_forbidden, "四四禁手")
        
        success = self.board.place_piece(7, 7, Board.BLACK)
        self.assertFalse(success)

    def test_black_five_wins_overrides_forbidden(self):
        """Test that if a move makes five-in-a-row, it wins and is not forbidden (even if it looks like a double-three)."""
        # Set up a potential five-in-a-row: (7, 3) to (7, 6) -> Placing at (7, 7) makes 5.
        self.board.grid[7][3] = Board.BLACK
        self.board.grid[7][4] = Board.BLACK
        self.board.grid[7][5] = Board.BLACK
        self.board.grid[7][6] = Board.BLACK
        
        # Set up an open three vertically: (5, 7), (6, 7) -> Placing at (7, 7) makes 3.
        self.board.grid[5][7] = Board.BLACK
        self.board.grid[6][7] = Board.BLACK
        
        # Placed at (7, 7) is a win (5 in a row), bypassing double-three checks.
        is_forbidden = self.board.check_forbidden_move(7, 7)
        self.assertIsNone(is_forbidden)
        
        success = self.board.place_piece(7, 7, Board.BLACK)
        self.assertTrue(success)

    # --- White Player (No Restrictions) ---

    def test_white_no_overline_restriction(self):
        """Test that White is not restricted by overlines and can win with 6+ stones."""
        for c in range(1, 6):
            self.board.grid[7][c] = Board.WHITE
        
        # Placing at (7, 6) creates a 6-stone overline, which is legal and winning for White.
        is_forbidden = self.board.check_forbidden_move(7, 6) # None (check_forbidden_move is only called for Black in game loop, but let's check place_piece)
        success = self.board.place_piece(7, 6, Board.WHITE)
        self.assertTrue(success)
        self.assertTrue(self.board.check_winner(7, 6))

    def test_white_no_double_three_restriction(self):
        """Test that White can play double threes."""
        self.board.grid[5][7] = Board.WHITE
        self.board.grid[6][7] = Board.WHITE
        self.board.grid[7][5] = Board.WHITE
        self.board.grid[7][6] = Board.WHITE

        # White should successfully place at (7, 7)
        success = self.board.place_piece(7, 7, Board.WHITE)
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
