from enum import Enum, auto
from dataclasses import dataclass

class GameMode(Enum):
    PLAYER = auto()
    AI = auto()

class GameStatus(Enum):
    PLAYING = auto()
    WON = auto()
    LOST = auto()

class GamePhase(Enum):
    MENU = auto()
    PLAYING = auto()

@dataclass
class GameState:
    level_key: str
    mode: GameMode
    status: GameStatus = GameStatus.PLAYING
    phase: GamePhase = GamePhase.PLAYING
    first_click: bool = False

    def reset_for_restart(self):
        self.status = GameStatus.PLAYING
        self.phase = GamePhase.PLAYING
        self.first_click = False
