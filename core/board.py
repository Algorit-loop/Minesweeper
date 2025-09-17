import random
from collections import deque

class Cell:
    __slots__ = ("is_mine", "revealed", "flagged", "adj")
    def __init__(self):
        self.is_mine = False
        self.revealed = False
        self.flagged = False
        self.adj = 0

class Board:
    def __init__(self, rows: int, cols: int, mines: int):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.grid = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.generated = False
        self.flags = 0

    # ---- helpers
    def inb(self, r, c): return 0 <= r < self.rows and 0 <= c < self.cols
    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0: continue
                rr, cc = r + dr, c + dc
                if self.inb(rr, cc): yield rr, cc
    def is_revealed(self, r, c): return self.grid[r][c].revealed
    def is_flagged(self, r, c): return self.grid[r][c].flagged
    def is_mine(self, r, c): return self.grid[r][c].is_mine
    def adj_mines(self, r, c): return self.grid[r][c].adj
    def remaining_mines(self): return max(0, self.mines - self.flags)

    def numbers_cells(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.revealed and cell.adj > 0:
                    yield (r, c)

    def unknown_cells(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if not cell.revealed and not cell.flagged:
                    yield (r, c)

    def reset(self):
        self.grid = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
        self.generated = False
        self.flags = 0

    # ---- generation (always safe on first click)
    def _place_mines_safe(self, safe_r, safe_c):
        forbidden = {(safe_r, safe_c), *set(self.neighbors(safe_r, safe_c))}
        pool = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in forbidden]
        mine_positions = random.sample(pool, self.mines)
        for (r, c) in mine_positions:
            self.grid[r][c].is_mine = True
        # compute adj
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine: continue
                self.grid[r][c].adj = sum(1 for (rr, cc) in self.neighbors(r, c) if self.grid[rr][cc].is_mine)

    # ---- actions
    def reveal(self, r, c):
        """Reveal a cell. First ever reveal is guaranteed safe. Returns (hit_mine, any_change)."""
        if not self.inb(r, c): return (False, False)
        cell = self.grid[r][c]
        if cell.revealed or cell.flagged: return (False, False)

        if not self.generated:
            self._place_mines_safe(r, c)
            self.generated = True

        cell = self.grid[r][c]
        if cell.is_mine:
            cell.revealed = True
            return (True, True)

        changed = self._flood_open(r, c)
        return (False, changed)

    def _flood_open(self, sr, sc):
        if self.grid[sr][sc].revealed: return False
        q = deque([(sr, sc)])
        changed = False
        while q:
            r, c = q.popleft()
            cell = self.grid[r][c]
            if cell.revealed or cell.flagged: continue
            cell.revealed = True
            changed = True
            if cell.adj == 0:
                for (rr, cc) in self.neighbors(r, c):
                    if not self.grid[rr][cc].revealed and not self.grid[rr][cc].flagged:
                        q.append((rr, cc))
        return changed

    def toggle_flag(self, r, c):
        if not self.inb(r, c): return
        cell = self.grid[r][c]
        if cell.revealed: return
        cell.flagged = not cell.flagged
        self.flags += 1 if cell.flagged else -1

    def reveal_all_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine:
                    self.grid[r][c].revealed = True

    def check_win(self):
        total = self.rows * self.cols - self.mines
        opened = sum(1 for r in range(self.rows) for c in range(self.cols)
                     if self.grid[r][c].revealed and not self.grid[r][c].is_mine)
        return opened == total
