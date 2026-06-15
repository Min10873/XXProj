import unittest
import json
from app import app, game_state
from board import Board

class TestGomokuAPI(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        # Reset game state before each test
        self.client.post('/api/new_game')

    def test_new_game(self):
        """Test game initialization endpoint."""
        response = self.client.post('/api/new_game')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['winner'], 0)
        self.assertEqual(data['reason'], 'active')
        self.assertEqual(data['current_player'], Board.BLACK)
        self.assertEqual(len(data['moves']), 0)
        self.assertEqual(len(data['board']), Board.SIZE)
        self.assertEqual(len(data['board'][0]), Board.SIZE)

    def test_place_piece_success(self):
        """Test valid piece placement."""
        response = self.client.post('/api/place', json={"row": 7, "col": 7})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['board'][7][7], Board.BLACK)
        self.assertEqual(data['current_player'], Board.WHITE)
        self.assertEqual(len(data['moves']), 1)
        self.assertEqual(data['moves'][0]['pos'], [8, 8])  # 1-based pos index

    def test_place_piece_occupied(self):
        """Test placing piece on an occupied spot returns 400."""
        self.client.post('/api/place', json={"row": 7, "col": 7})
        # Try placing again at same spot
        response = self.client.post('/api/place', json={"row": 7, "col": 7})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn("已有棋子", data['message'])

    def test_place_piece_invalid_params(self):
        """Test placing piece with invalid parameter payloads."""
        # Missing parameter
        response = self.client.post('/api/place', json={"row": 7})
        self.assertEqual(response.status_code, 400)
        
        # String coordinate
        response = self.client.post('/api/place', json={"row": "seven", "col": 7})
        self.assertEqual(response.status_code, 400)

    def test_place_piece_out_of_bounds(self):
        """Test placing piece outside coordinates boundaries."""
        response = self.client.post('/api/place', json={"row": -1, "col": 0})
        self.assertEqual(response.status_code, 400)
        
        response = self.client.post('/api/place', json={"row": 15, "col": 0})
        self.assertEqual(response.status_code, 400)

    def test_black_overline_restriction(self):
        """Test Black is forbidden from creating an overline (6+ stones)."""
        # Set up 5 black stones manually in board state
        game_state.board.grid[7][1] = Board.BLACK
        game_state.board.grid[7][2] = Board.BLACK
        game_state.board.grid[7][3] = Board.BLACK
        game_state.board.grid[7][4] = Board.BLACK
        game_state.board.grid[7][5] = Board.BLACK
        game_state.current_player = Board.BLACK

        # Placing at (7, 6) would make 6-in-a-row (overline)
        response = self.client.post('/api/place', json={"row": 7, "col": 6})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['forbidden_type'], '长连禁手')

    def test_black_double_three_restriction(self):
        """Test Black is forbidden from creating double threes (三三禁手)."""
        # Setup vertical three parts: (5, 7), (6, 7)
        game_state.board.grid[5][7] = Board.BLACK
        game_state.board.grid[6][7] = Board.BLACK
        # Setup horizontal three parts: (7, 5), (7, 6)
        game_state.board.grid[7][5] = Board.BLACK
        game_state.board.grid[7][6] = Board.BLACK
        game_state.current_player = Board.BLACK

        # (7, 7) triggers double three
        response = self.client.post('/api/place', json={"row": 7, "col": 7})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['forbidden_type'], '三三禁手')

    def test_black_double_four_restriction(self):
        """Test Black is forbidden from creating double fours (四四禁手)."""
        # Setup vertical four: (4, 7), (5, 7), (6, 7)
        game_state.board.grid[4][7] = Board.BLACK
        game_state.board.grid[5][7] = Board.BLACK
        game_state.board.grid[6][7] = Board.BLACK
        # Setup horizontal four: (7, 4), (7, 5), (7, 6)
        game_state.board.grid[7][4] = Board.BLACK
        game_state.board.grid[7][5] = Board.BLACK
        game_state.board.grid[7][6] = Board.BLACK
        game_state.current_player = Board.BLACK

        # (7, 7) triggers double four
        response = self.client.post('/api/place', json={"row": 7, "col": 7})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['forbidden_type'], '四四禁手')

    def test_black_five_wins_override_forbidden(self):
        """Test Black 5-in-a-row overrides forbidden check."""
        # Setup four in a row: (7, 3), (7, 4), (7, 5), (7, 6)
        game_state.board.grid[7][3] = Board.BLACK
        game_state.board.grid[7][4] = Board.BLACK
        game_state.board.grid[7][5] = Board.BLACK
        game_state.board.grid[7][6] = Board.BLACK
        # Setup open three: (5, 7), (6, 7)
        game_state.board.grid[5][7] = Board.BLACK
        game_state.board.grid[6][7] = Board.BLACK
        game_state.current_player = Board.BLACK

        # Placing at (7, 7) completes five in a row (win), bypassing double three
        response = self.client.post('/api/place', json={"row": 7, "col": 7})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['winner'], Board.BLACK)
        self.assertEqual(data['reason'], 'five_in_a_row')

    def test_white_no_overline_restriction(self):
        """Test White is not subject to overline restrictions and wins with 6+ stones."""
        game_state.board.grid[7][1] = Board.WHITE
        game_state.board.grid[7][2] = Board.WHITE
        game_state.board.grid[7][3] = Board.WHITE
        game_state.board.grid[7][4] = Board.WHITE
        game_state.board.grid[7][5] = Board.WHITE
        game_state.current_player = Board.WHITE

        # White placing at (7, 6) should succeed and win
        response = self.client.post('/api/place', json={"row": 7, "col": 6})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['winner'], Board.WHITE)
        self.assertEqual(data['reason'], 'five_in_a_row')

    def test_undo_state_rollback(self):
        """Test undoing moves rolls back the game state correctly."""
        # Make a move
        self.client.post('/api/place', json={"row": 7, "col": 7})
        
        # Undo move
        response = self.client.post('/api/undo')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['board'][7][7], Board.EMPTY)
        self.assertEqual(data['current_player'], Board.BLACK)
        self.assertEqual(len(data['moves']), 0)

    def test_undo_empty(self):
        """Test undoing when no moves have been made returns 400."""
        response = self.client.post('/api/undo')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')

    def test_save_game_json_format(self):
        """Test save endpoint format matches the required schema template."""
        # Play one move
        self.client.post('/api/place', json={"row": 7, "col": 7})
        
        response = self.client.get('/api/save')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify keys
        self.assertIn("game_id", data)
        self.assertIn("date", data)
        self.assertIn("players", data)
        self.assertIn("board_size", data)
        self.assertIn("moves", data)
        self.assertIn("result", data)
        
        # Verify sub-elements
        self.assertEqual(data['board_size'], 15)
        self.assertEqual(len(data['moves']), 1)
        self.assertEqual(data['moves'][0]['step'], 1)
        self.assertEqual(data['moves'][0]['player'], Board.BLACK)
        self.assertEqual(data['moves'][0]['pos'], [8, 8])
        self.assertIn("time_spent", data['moves'][0])
        self.assertEqual(data['result']['winner'], 0)
        self.assertEqual(data['result']['reason'], 'active')

if __name__ == '__main__':
    unittest.main()
