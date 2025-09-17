import pygame
from config import TILE, HUD, COLORS, FACE

# -------- Fonts (Ưu tiên Segoe UI cho tiếng Việt)
_UI_FONT_NAMES = ["segoe ui", "arial", "tahoma", "dejavu sans", "noto sans"]
def _match_font():
    for name in _UI_FONT_NAMES:
        path = pygame.font.match_font(name)
        if path:
            return path
    return None

_FONT_PATH = None
def get_font(px, bold=False):
    global _FONT_PATH
    if _FONT_PATH is None:
        _FONT_PATH = _match_font()
    if _FONT_PATH:
        f = pygame.font.Font(_FONT_PATH, px)
        f.set_bold(bold)
        return f
    return pygame.font.SysFont(None, px, bold=bold)

def compute_window_size(rows, cols):
    board_w = cols * (TILE["size"] + TILE["gap"]) + TILE["gap"]
    board_h = rows * (TILE["size"] + TILE["gap"]) + TILE["gap"]
    w = max(board_w, 540)
    h = HUD["height"] + board_h
    return (w, h)

def board_origin(rows, cols, screen_w):
    board_w = cols * (TILE["size"] + TILE["gap"]) + TILE["gap"]
    x = (screen_w - board_w) // 2
    y = HUD["height"]
    return x, y

def face_button_rect(screen_w):
    size = HUD["face_size"]
    x = (screen_w - size) // 2
    y = (HUD["height"] - size) // 2
    return pygame.Rect(x, y, size, size)

def _draw_smiley(surface, rect, mood="neutral"):
    # nền nút
    pygame.draw.rect(surface, (70,70,70), rect, border_radius=14)
    pygame.draw.rect(surface, (30,30,30), rect, 2, border_radius=14)

    # mặt (vector) trong rect
    cx, cy = rect.center
    r = rect.height // 2 - 8
    # đầu
    pygame.draw.circle(surface, (220,220,220), (cx, cy), r)
    pygame.draw.circle(surface, (40,40,40), (cx, cy), r, 2)
    # mắt
    eye_dx = r//2
    eye_r = max(2, r//7)
    if mood == "lost":
        # mắt X
        for ex in (cx - eye_dx, cx + eye_dx):
            pygame.draw.line(surface, (20,20,20), (ex-6, cy-6), (ex+6, cy+6), 3)
            pygame.draw.line(surface, (20,20,20), (ex+6, cy-6), (ex-6, cy+6), 3)
    else:
        pygame.draw.circle(surface, (20,20,20), (cx - eye_dx, cy - 3), eye_r)
        pygame.draw.circle(surface, (20,20,20), (cx + eye_dx, cy - 3), eye_r)
        if mood == "win":
            # kính mát
            g_rect = pygame.Rect(cx - eye_dx - 10, cy - 10, 2*(eye_dx+10), 14)
            pygame.draw.rect(surface, (25,25,25), g_rect, border_radius=6)

    # miệng
    if mood == "neutral":
        pygame.draw.line(surface, (20,20,20), (cx - r//2, cy + r//3), (cx + r//2, cy + r//3), 3)
    elif mood == "lost":
        pygame.draw.arc(surface, (20,20,20),
                        (cx - r//2, cy + r//6, r, r//1.4), 3.5, 6.0, 3)
    else:  # win
        pygame.draw.arc(surface, (20,20,20),
                        (cx - r//2, cy, r, r//1.2), 3.8, 5.6, 3)

def draw_face_button(surface, face_char):
    mood = "neutral" if face_char == FACE["neutral"] else ("lost" if face_char == FACE["lost"] else "win")
    _draw_smiley(surface, face_button_rect(surface.get_width()), mood)

def draw_board(surface, board, state):
    rows, cols = board.rows, board.cols
    ox, oy = board_origin(rows, cols, surface.get_width())

    board_w = cols * (TILE["size"] + TILE["gap"]) + TILE["gap"]
    board_h = rows * (TILE["size"] + TILE["gap"]) + TILE["gap"]
    pygame.draw.rect(surface, COLORS["grid_bg"], (ox, oy, board_w, board_h), border_radius=8)

    font = get_font(TILE["font_px"], bold=True)

    for r in range(rows):
        for c in range(cols):
            x = ox + TILE["gap"] + c*(TILE["size"]+TILE["gap"])
            y = oy + TILE["gap"] + r*(TILE["size"]+TILE["gap"])
            rect = pygame.Rect(x, y, TILE["size"], TILE["size"])
            cell = board.grid[r][c]

            if cell.revealed:
                base = COLORS["tile_open"] if (r+c)%2==0 else COLORS["tile_open_alt"]
                pygame.draw.rect(surface, base, rect, border_radius=6)
                pygame.draw.rect(surface, COLORS["border"], rect, 1, border_radius=6)
                if cell.is_mine:
                    pygame.draw.circle(surface, (20,20,20), rect.center, TILE["size"]//3)
                    pygame.draw.circle(surface, (255,70,70), rect.center, TILE["size"]//3, 3)
                elif cell.adj > 0:
                    color = COLORS["number"][cell.adj]
                    img = font.render(str(cell.adj), True, color)
                    surface.blit(img, img.get_rect(center=rect.center))
            else:
                pygame.draw.rect(surface, COLORS["tile"], rect, border_radius=6)
                pygame.draw.rect(surface, COLORS["border"], rect, 1, border_radius=6)
                if cell.flagged:
                    # vẽ cờ đơn giản (tam giác)
                    p1 = (rect.centerx, rect.top + 6)
                    p2 = (rect.centerx, rect.top + rect.height//2)
                    p3 = (rect.centerx + rect.width//3, rect.top + rect.height//3)
                    pygame.draw.polygon(surface, (220,40,40), [p1, p2, p3])
                    pygame.draw.line(surface, (35,35,35), (rect.centerx, rect.top+4), (rect.centerx, rect.bottom-6), 2)

def draw_menu(surface, phase="level", return_click=False, mouse=None):
    surface.fill((24,24,24))
    title = "MINESWEEPER"
    sub1 = "Chọn Level (1–5)"
    sub2 = "Sau đó chọn Chế độ: Player hoặc AI"

    font_title = get_font(56, bold=True)
    font_sub = get_font(24)

    center_x = surface.get_width() // 2
    y = 40
    img = font_title.render(title, True, (235,235,235))
    surface.blit(img, img.get_rect(midtop=(center_x, y)))
    y += 80

    if phase == "level":
        surface.blit(font_sub.render(sub1, True, (200,200,200)),
                     font_sub.render(sub1, True, (200,200,200)).get_rect(midtop=(center_x, y)))
        y += 50
        btns = []
        for i in range(1,6):
            rect = pygame.Rect(center_x - 240 + (i-1)*120, y, 90, 62)
            pygame.draw.rect(surface, (80,80,80), rect, border_radius=12)
            pygame.draw.rect(surface, (30,30,30), rect, 2, border_radius=12)
            txt = get_font(32, bold=True).render(str(i), True, (245,245,245))
            surface.blit(txt, txt.get_rect(center=rect.center))
            btns.append((str(i), rect))
        if return_click and mouse:
            mx, my = mouse
            for key, rect in btns:
                if rect.collidepoint(mx, my): return key
    else:
        surface.blit(font_sub.render(sub2, True, (200,200,200)),
                     font_sub.render(sub2, True, (200,200,200)).get_rect(midtop=(center_x, y)))
        y += 56
        player_rect = pygame.Rect(center_x - 170, y, 150, 62)
        ai_rect     = pygame.Rect(center_x + 20,  y, 150, 62)
        for rect, label in [(player_rect, "Player"), (ai_rect, "AI")]:
            pygame.draw.rect(surface, (80,80,80), rect, border_radius=12)
            pygame.draw.rect(surface, (30,30,30), rect, 2, border_radius=12)
            txt = get_font(28, bold=True).render(label, True, (245,245,245))
            surface.blit(txt, txt.get_rect(center=rect.center))
        if return_click and mouse:
            mx, my = mouse
            if player_rect.collidepoint(mx,my): return "player"
            if ai_rect.collidepoint(mx,my): return "ai"
    return None
