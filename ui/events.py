from config import TILE, HUD

def pos_to_cell(mx, my, rows, cols):
    # Convert mouse position to (r,c) on board; returns None if outside board
    # Board is centered horizontally; we recompute origin same as display.py
    board_w = cols * (TILE["size"] + TILE["gap"]) + TILE["gap"]
    ox = (max(board_w, 420) - board_w) // 2  # this only works if screen width == compute_window_size(...)[0]
    # BUT main centers using screen width; recalc origin same way:
    # We'll re-derive: actual screen width is unknown here; so we accept approx by recomputing using given board_w.
    # To ensure correctness, we do not use this ox. Instead, the main computes accurately.
    # => We expose a simpler variant: assume we were passed true screen size; however, we aren't.
    # Practical workaround: rely on main to call pos_to_cell only after it sets display; but we still need true ox.
    # We'll compute ox = (screen_w - board_w)//2 in main instead; hence we move this function usage to main?
    # For simplicity, keep here and expect main passes global pygame.display.get_surface() to derive screen_w:
    import pygame
    surface = pygame.display.get_surface()
    screen_w = surface.get_width()
    ox = (screen_w - board_w) // 2

    oy = HUD["height"]
    if not (ox <= mx <= ox + board_w and oy <= my <= oy + rows * (TILE["size"]+TILE["gap"]) + TILE["gap"]):
        return None

    rel_x = mx - ox - TILE["gap"]
    rel_y = my - oy - TILE["gap"]
    if rel_x < 0 or rel_y < 0:
        return None
    col = rel_x // (TILE["size"] + TILE["gap"])
    row = rel_y // (TILE["size"] + TILE["gap"])
    # ensure inside tile content not in gaps
    x_in = rel_x % (TILE["size"] + TILE["gap"])
    y_in = rel_y % (TILE["size"] + TILE["gap"])
    if x_in >= TILE["size"] or y_in >= TILE["size"]:
        return None
    if 0 <= row < rows and 0 <= col < cols:
        return (int(row), int(col))
    return None
