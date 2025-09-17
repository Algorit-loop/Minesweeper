from dataclasses import dataclass

# -------- LEVELS (5 mức) --------
LEVELS = {
    # Beginner
    "1": {"rows": 9,  "cols": 9,  "mines": 10},
    # Easy+
    "2": {"rows": 12, "cols": 12, "mines": 20},
    # Intermediate
    "3": {"rows": 16, "cols": 16, "mines": 40},
    # Hard
    "4": {"rows": 20, "cols": 24, "mines": 80},
    # Expert (classic)
    "5": {"rows": 16, "cols": 30, "mines": 99},
}

# -------- COLORS --------
COLORS = {
    "bg": (28, 28, 28),
    "hud_bg": (18, 18, 18),
    "grid_bg": (40, 40, 40),
    "tile": (65, 65, 65),
    "tile_open": (210, 210, 210),
    "tile_open_alt": (195, 195, 195),
    "border": (15, 15, 15),
    "flag": (220, 30, 30),
    "mine": (12, 12, 12),
    "text": (20, 20, 20),
    "hud_text": (235, 235, 235),
    "number": {
        1: (25, 118, 210),
        2: (56, 142, 60),
        3: (211, 47, 47),
        4: (123, 31, 162),
        5: (255, 143, 0),
        6: (0, 151, 167),
        7: (97, 97, 97),
        8: (0, 0, 0),
    },
}

# -------- TILE/HUD --------
TILE = {
    "size": 32,
    "gap": 2,
    "font_px": 20,
}
HUD = {
    "height": 80,
    "padding": 16,
    "face_size": 48,
    "font_px": 28,
}

# -------- FACE ICONS (emoji/text) --------
FACE = {
    "neutral": "🙂",
    "lost": "😵",
    "win": "😎",
}

# -------- AI CONFIG --------
AI = {
    "step_ms": 70  # tốc độ AI (ms mỗi nhịp)
}
