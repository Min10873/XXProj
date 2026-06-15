import os
from PIL import Image, ImageDraw, ImageFont

class BoardRenderer:
    SIZE = 600
    PADDING = 40
    GRID_SIZE = 15
    CELL_SPACING = (SIZE - 2 * PADDING) / (GRID_SIZE - 1)

    BG_COLOR = (11, 15, 23)        # #0b0f17
    GRID_COLOR = (45, 55, 72)      # #2d3748
    TEXT_COLOR = (144, 164, 174)   # #90a4ae
    ACCENT_CYAN = (0, 242, 254)    # #00f2fe
    ACCENT_PINK = (253, 56, 127)   # #fd387f
    ACCENT_GOLD = (255, 215, 0)    # #ffd700

    def __init__(self):
        # Load font
        try:
            # Arial standard font on Windows
            self.font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 12)
            self.font_bold = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 13)
            self.font_large = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 16)
        except Exception:
            self.font = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()
            self.font_large = ImageFont.load_default()

    def get_coords(self, r, c):
        """Convert row/col indices (0-14) to canvas (x, y) coordinates."""
        x = self.PADDING + c * self.CELL_SPACING
        y = self.PADDING + r * self.CELL_SPACING
        return x, y

    def draw_board(self, grid, last_move=None, forbidden_move=None, forbidden_type=None, winning_line=None, winner=None):
        """
        Draws the board state to a PIL Image.
        - grid: 15x15 2D array
        - last_move: tuple (row, col)
        - forbidden_move: tuple (row, col)
        - forbidden_type: string (e.g. "三三禁手")
        - winning_line: list of tuples [(r1,c1), ..., (r5,c5)]
        - winner: int (1 for Black, 2 for White)
        """
        # Create base image
        img = Image.new("RGB", (self.SIZE, self.SIZE), self.BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 1. Draw grid lines
        for i in range(self.GRID_SIZE):
            # Horizontal lines
            x1, y1 = self.get_coords(i, 0)
            x2, y2 = self.get_coords(i, self.GRID_SIZE - 1)
            draw.line([(x1, y1), (x2, y2)], fill=self.GRID_COLOR, width=1)

            # Vertical lines
            x1, y1 = self.get_coords(0, i)
            x2, y2 = self.get_coords(self.GRID_SIZE - 1, i)
            draw.line([(x1, y1), (x2, y2)], fill=self.GRID_COLOR, width=1)

        # 2. Draw star points (星位)
        stars = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
        for r, c in stars:
            x, y = self.get_coords(r, c)
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(100, 110, 125))

        # 3. Draw coordinate labels (A-O on cols, 1-15 on rows)
        cols_labels = "ABCDEFGHIJKLMNO"
        for i in range(self.GRID_SIZE):
            x, y = self.get_coords(0, i)
            # Top letters
            draw.text((x, self.PADDING - 20), cols_labels[i], fill=self.TEXT_COLOR, font=self.font, anchor="mm")
            # Bottom letters
            draw.text((x, self.SIZE - self.PADDING + 20), cols_labels[i], fill=self.TEXT_COLOR, font=self.font, anchor="mm")

            x, y = self.get_coords(i, 0)
            # Left numbers
            draw.text((self.PADDING - 20, y), str(i + 1), fill=self.TEXT_COLOR, font=self.font, anchor="mm")
            # Right numbers
            draw.text((self.SIZE - self.PADDING + 20, y), str(i + 1), fill=self.TEXT_COLOR, font=self.font, anchor="mm")

        # 4. Draw pieces
        radius = self.CELL_SPACING * 0.42
        for r in range(self.GRID_SIZE):
            for c in range(self.GRID_SIZE):
                val = grid[r][c]
                if val == 0:
                    continue
                x, y = self.get_coords(r, c)
                
                # Simple radial gradient imitation for 3D effect
                if val == 1:  # Black
                    # Draw main black circle
                    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(20, 20, 20), outline=(50, 50, 50), width=1)
                    # Draw reflection highlight
                    draw.ellipse([x - radius/2, y - radius/2, x - radius/6, y - radius/6], fill=(90, 90, 90))
                elif val == 2:  # White
                    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(240, 240, 240), outline=(180, 180, 180), width=1)
                    draw.ellipse([x - radius/2, y - radius/2, x - radius/6, y - radius/6], fill=(255, 255, 255))

        # 5. Highlight last move
        if last_move:
            r, c = last_move
            x, y = self.get_coords(r, c)
            # Draw glow ring
            glow_color = self.ACCENT_CYAN if grid[r][c] == 1 else self.ACCENT_PINK
            draw.ellipse([x - radius - 3, y - radius - 3, x + radius + 3, y + radius + 3], outline=glow_color, width=2)

        # 6. Draw forbidden move preview and tooltip
        if forbidden_move and forbidden_type:
            r, c = forbidden_move
            x, y = self.get_coords(r, c)
            # Draw red dashed circle outline representation
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(253, 56, 127, 80), outline=self.ACCENT_PINK, width=2)
            # Draw "禁" text
            draw.text((x, y), "禁", fill=(255, 255, 255), font=self.font_bold, anchor="mm")
            
            # Tooltip block
            tooltip = f"黑棋: {forbidden_type}"
            t_w = 110
            t_h = 24
            tx = x - t_w / 2
            ty = y - radius - t_h - 6
            # Tooltip background
            draw.rounded_rectangle([tx, ty, tx + t_w, ty + t_h], radius=5, fill=self.ACCENT_PINK)
            # Tooltip text
            draw.text((x, ty + t_h / 2), tooltip, fill=(255, 255, 255), font=self.font_bold, anchor="mm")

        # 7. Draw winning line and glow
        if winning_line:
            points = [self.get_coords(r, c) for r, c in winning_line]
            # Draw semi-transparent thick winning line
            draw.line(points, fill=self.ACCENT_GOLD, width=6)
            # Highlight individual winning pieces
            for r, c in winning_line:
                x, y = self.get_coords(r, c)
                draw.ellipse([x - radius - 2, y - radius - 2, x + radius + 2, y + radius + 2], outline=self.ACCENT_GOLD, width=3)

        # 8. Draw Winner overlay panel
        if winner:
            winner_str = "Winner: Black (●)" if winner == 1 else "Winner: White (○)"
            # Info box
            box_w, box_h = 200, 36
            bx, by = self.SIZE - box_w - 20, 20
            draw.rounded_rectangle([bx, by, bx + box_w, by + box_h], radius=8, fill=(30, 41, 59))
            draw.text((bx + box_w/2, by + box_h/2), winner_str, fill=self.ACCENT_GOLD, font=self.font_large, anchor="mm")

        return img
