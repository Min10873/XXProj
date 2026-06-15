class Board:
    SIZE = 15
    EMPTY = 0
    BLACK = 1
    WHITE = 2

    def __init__(self):
        self.grid = [[self.EMPTY for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.last_move = None

    def is_valid_move(self, row, col, player=None):
        """
        Check if the move is within boundaries, the cell is empty,
        and (if player is BLACK) does not violate Renju restrictions.
        """
        if not (0 <= row < self.SIZE and 0 <= col < self.SIZE):
            return False
        if self.grid[row][col] != self.EMPTY:
            return False
        
        # If player is BLACK, check Renju restrictions
        if player == self.BLACK:
            if self.check_forbidden_move(row, col):
                return False
                
        return True

    def place_piece(self, row, col, player):
        """Place a piece on the board. Returns True if successful, False otherwise."""
        if self.is_valid_move(row, col, player):
            self.grid[row][col] = player
            self.last_move = (row, col)
            return True
        return False

    def check_winner(self, row, col):
        """Check if the last placed piece at (row, col) forms a line of 5 or more (for white) or exactly 5 (for black)."""
        player = self.grid[row][col]
        if player == self.EMPTY:
            return False

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1
            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.SIZE and 0 <= c < self.SIZE and self.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
                
            # Negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.SIZE and 0 <= c < self.SIZE and self.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            # For Black, exactly 5 is a win. More than 5 (overline) is a forbidden move.
            # For White, 5 or more is a win.
            if player == self.BLACK and count == 5:
                return True
            elif player == self.WHITE and count >= 5:
                return True

        return False

    def check_overline(self, row, col, player):
        """Check if placing player's stone at (row, col) creates an overline (6+ stones)."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            r, c = row + dr, col + dc
            while 0 <= r < self.SIZE and 0 <= c < self.SIZE and self.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            r, c = row - dr, col - dc
            while 0 <= r < self.SIZE and 0 <= c < self.SIZE and self.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 6:
                return True
        return False

    def get_line_segment(self, row, col, dr, dc, length=9):
        """
        Helper to get a line segment of cells centered at (row, col) in direction (dr, dc).
        Returns a list of tuples (r, c, val) where val is the cell value, or None if out of bounds.
        """
        segment = []
        half = length // 2
        for i in range(-half, half + 1):
            r, c = row + i * dr, col + i * dc
            if 0 <= r < self.SIZE and 0 <= c < self.SIZE:
                segment.append((r, c, self.grid[r][c]))
            else:
                segment.append(None)
        return segment

    def count_open_threes(self, row, col):
        """
        Count the number of open threes (活三) created by placing Black at (row, col).
        """
        open_three_count = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        # Temporarily place Black
        self.grid[row][col] = self.BLACK

        for dr, dc in directions:
            # Get 9-cell segment around (row, col)
            segment = self.get_line_segment(row, col, dr, dc, length=9)
            # Find if there is any 6-cell window that contains the new stone (row, col)
            # and matches one of the open three patterns:
            # [0, 0, 1, 1, 1, 0], [0, 1, 0, 1, 1, 0], [0, 1, 1, 0, 1, 0], [0, 1, 1, 1, 0, 0]
            # representation: 0=EMPTY, 1=BLACK
            found_open_three = False
            for start in range(4):  # Windows of length 6: indices 0..5, 1..6, 2..7, 3..8
                window = segment[start : start + 6]
                if None in window:
                    continue
                
                # Check if this window contains (row, col)
                coords = [(item[0], item[1]) for item in window]
                if (row, col) not in coords:
                    continue

                vals = [item[2] for item in window]
                # Check patterns
                if vals in [
                    [self.EMPTY, self.EMPTY, self.BLACK, self.BLACK, self.BLACK, self.EMPTY],
                    [self.EMPTY, self.BLACK, self.EMPTY, self.BLACK, self.BLACK, self.EMPTY],
                    [self.EMPTY, self.BLACK, self.BLACK, self.EMPTY, self.BLACK, self.EMPTY],
                    [self.EMPTY, self.BLACK, self.BLACK, self.BLACK, self.EMPTY, self.EMPTY]
                ]:
                    found_open_three = True
                    break
            
            if found_open_three:
                open_three_count += 1

        # Revert
        self.grid[row][col] = self.EMPTY
        return open_three_count

    def count_fours(self, row, col):
        """
        Count the number of fours (活四 or 冲四) created by placing Black at (row, col).
        """
        four_count = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        # Temporarily place Black
        self.grid[row][col] = self.BLACK

        for dr, dc in directions:
            segment = self.get_line_segment(row, col, dr, dc, length=9)
            found_four = False
            # Find if there is any 5-cell window containing (row, col) with exactly 4 Black stones and 1 EMPTY
            for start in range(5):  # Windows of length 5: indices 0..4, 1..5, 2..6, 3..7, 4..8
                window = segment[start : start + 5]
                if None in window:
                    continue
                
                coords = [(item[0], item[1]) for item in window]
                if (row, col) not in coords:
                    continue

                vals = [item[2] for item in window]
                # Check if there are exactly 4 BLACK and 1 EMPTY
                if vals.count(self.BLACK) == 4 and vals.count(self.EMPTY) == 1:
                    found_four = True
                    break
            
            if found_four:
                four_count += 1

        # Revert
        self.grid[row][col] = self.EMPTY
        return four_count

    def check_forbidden_move(self, row, col):
        """
        Verify if placing Black at (row, col) is a forbidden move (禁手) under Renju rules.
        Returns the type of forbidden move as a string, or None if it's legal.
        """
        # If it immediately forms a 5-in-a-row, it is NOT forbidden (bypasses all checks)
        # Temporarily place Black to check winner
        self.grid[row][col] = self.BLACK
        is_win = self.check_winner(row, col)
        self.grid[row][col] = self.EMPTY
        if is_win:
            return None

        # 1. Overline (长连)
        if self.check_overline(row, col, self.BLACK):
            return "长连禁手"

        # 2. Double Three (三三)
        if self.count_open_threes(row, col) >= 2:
            return "三三禁手"

        # 3. Double Four (四四)
        if self.count_fours(row, col) >= 2:
            return "四四禁手"

        return None

    def is_full(self):
        """Check if the board is completely filled (draw game)."""
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if self.grid[r][c] == self.EMPTY:
                    return False
        return True
