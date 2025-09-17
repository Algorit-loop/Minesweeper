import pygame
from config import HUD, COLORS
from .display import draw_face_button, get_font

def draw_hud(surface, board, timer, state, face_char):
    rect = pygame.Rect(0, 0, surface.get_width(), HUD["height"])
    pygame.draw.rect(surface, COLORS["hud_bg"], rect)

    font = get_font(HUD["font_px"], bold=True)

    # MINES (left)
    bombs = board.remaining_mines()
    left_txt = font.render(f"MINES {bombs:03d}", True, COLORS["hud_text"])
    surface.blit(left_txt, (HUD["padding"], (HUD["height"] - left_txt.get_height())//2))

    # TIME (right)
    secs = timer.seconds()
    right_txt = font.render(f"TIME {secs:03d}", True, COLORS["hud_text"])
    surface.blit(right_txt, (surface.get_width() - HUD["padding"] - right_txt.get_width(),
                             (HUD["height"] - right_txt.get_height())//2))

    # FACE (center)
    draw_face_button(surface, face_char)
