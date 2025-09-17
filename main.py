import os
import sys
import pygame

# Ensure package imports when running as script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from config import LEVELS, COLORS, TILE, HUD, AI as AI_CFG, FACE
from core.board import Board
from core.timer import GameTimer
from core.game_state import GameMode, GameStatus, GamePhase, GameState
from ui.display import draw_board, draw_menu, draw_face_button, compute_window_size, face_button_rect
from ui.hud import draw_hud
from ui.events import pos_to_cell
from ai.ai import MinesweeperAI
from ui.display import draw_board, draw_menu, draw_face_button, compute_window_size, face_button_rect


pygame.init()
pygame.display.set_caption("Minesweeper")

def run_game():
    clock = pygame.time.Clock()

    # -------- MENU LOOP --------
    level_key, mode = show_menu(clock)

    # -------- INIT GAME --------
    cfg = LEVELS[level_key]
    rows, cols, mines = cfg["rows"], cfg["cols"], cfg["mines"]
    window_w, window_h = compute_window_size(rows, cols)
    screen = pygame.display.set_mode((window_w, window_h))

    board = Board(rows, cols, mines)
    timer = GameTimer()
    state = GameState(level_key=level_key, mode=mode)
    ai = MinesweeperAI() if mode == GameMode.AI else None
    ai_started = False
    face = FACE["neutral"]

    last_ai_step = 0

    running = True
    while running:
        dt = clock.tick(60)
        screen.fill(COLORS["bg"])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    # restart current game quickly
                    board.reset()
                    timer.reset()
                    state.reset_for_restart()
                    ai_started = False
                    face = FACE["neutral"]
                if event.key == pygame.K_m:
                    # back to menu
                    level_key, mode = show_menu(clock)
                    cfg = LEVELS[level_key]
                    rows, cols, mines = cfg["rows"], cfg["cols"], cfg["mines"]
                    window_w, window_h = compute_window_size(rows, cols)
                    screen = pygame.display.set_mode((window_w, window_h))
                    board = Board(rows, cols, mines)
                    timer = GameTimer()
                    state = GameState(level_key=level_key, mode=mode)
                    ai = MinesweeperAI() if mode == GameMode.AI else None
                    ai_started = False
                    face = FACE["neutral"]

            # Mouse in-game
            if state.phase == GamePhase.PLAYING and state.status == GameStatus.PLAYING:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos

                    if face_button_rect(screen.get_width()).collidepoint(mx, my):
                        board.reset(); timer.reset(); state.reset_for_restart()
                        ai_started = False; face = FACE["neutral"]; continue

                    cell = pos_to_cell(mx, my, rows, cols)
                    if cell is None: continue
                    r, c = cell

                    if event.button == 1:
                        if not state.first_click:
                            state.first_click = True
                            timer.start()
                        hit_mine, changed = board.reveal(r, c)  # <-- luôn safe click đầu
                        if hit_mine:
                            state.status = GameStatus.LOST; timer.stop(); face = FACE["lost"]; board.reveal_all_mines()
                        elif board.check_win():
                            state.status = GameStatus.WON; timer.stop(); face = FACE["win"]

                        if state.mode == GameMode.AI and state.first_click and not ai_started and state.status == GameStatus.PLAYING:
                            ai_started = True

                    if event.button == 3:
                        board.toggle_flag(r, c)
                        if board.check_win():
                            state.status = GameStatus.WON; timer.stop(); face = FACE["win"]

        # -------- AI AUTOPLAY --------
        if state.mode == GameMode.AI and ai_started and state.status == GameStatus.PLAYING:
            last_ai_step += dt
            if last_ai_step >= AI_CFG["step_ms"]:
                last_ai_step = 0
                # Run one AI step (may include multiple safe reveals/flags)
                actions = ai.next_actions(board)
                any_change = False

                # Apply flags first
                for (rr, cc) in actions["flags"]:
                    if not board.is_revealed(rr, cc) and not board.is_flagged(rr, cc):
                        board.toggle_flag(rr, cc)
                        any_change = True

                # Apply reveals
                for (rr, cc) in actions["reveal"]:
                    if not state.first_click:
                        state.first_click = True; timer.start()
                    hit_mine, changed = board.reveal(rr, cc)  # <-- safe-first đã qua
                    any_change = any_change or changed
                    if hit_mine:
                        state.status = GameStatus.LOST; timer.stop(); face = FACE["lost"]; board.reveal_all_mines(); break

                # If no deterministic actions, AI guesses 1 cell
                if state.status == GameStatus.PLAYING and not any_change:
                    guess = ai.guess(board)
                    if guess:
                        rr, cc = guess
                        hit_mine, _ = board.reveal(rr, cc)  # <-- gọi đơn giản
                        if hit_mine:
                            state.status = GameStatus.LOST; timer.stop(); face = FACE["lost"]; board.reveal_all_mines()

                if state.status == GameStatus.PLAYING and board.check_win():
                    state.status = GameStatus.WON
                    timer.stop()
                    face = FACE["win"]

        # -------- DRAW --------
        draw_hud(screen, board, timer, state, face)
        draw_board(screen, board, state)

        pygame.display.flip()

    pygame.quit()

def show_menu(clock):
    # Minimal menu window for selecting level & mode
    window_w, window_h = 1080, 720
    screen = pygame.display.set_mode((window_w, window_h))
    level_key = None
    mode = None

    phase = "level"  # "level" -> "mode"
    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if phase == "level":
                    clicked = draw_menu(screen, phase="level", return_click=True, mouse=(mx, my))
                    if clicked in LEVELS:
                        level_key = clicked
                        phase = "mode"
                elif phase == "mode":
                    clicked = draw_menu(screen, phase="mode", return_click=True, mouse=(mx, my))
                    if clicked == "player":
                        mode = GameMode.PLAYER
                        running = False
                    elif clicked == "ai":
                        mode = GameMode.AI
                        running = False

            if event.type == pygame.KEYDOWN:
                # Keyboard quick select: 1..5 for level, P/A for mode
                if phase == "level":
                    if event.unicode in LEVELS:
                        level_key = event.unicode
                        phase = "mode"
                else:
                    if event.unicode.lower() == "p":
                        mode = GameMode.PLAYER
                        running = False
                    if event.unicode.lower() == "a":
                        mode = GameMode.AI
                        running = False

        draw_menu(screen, phase=phase)
        pygame.display.flip()

    return level_key, mode

if __name__ == "__main__":
    run_game()
