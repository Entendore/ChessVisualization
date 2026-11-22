# ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from ui.board import BoardWidget
from ui.move_list import MoveListWidget
from ui.evaluation_bar import EvalBarWidget
from ui.player_info import PlayerInfoWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Visualizer (Chess, Shogi, Xiangqi)")
        self.resize(1400, 900)

        # === Central widget ===
        central = QWidget()
        self.setCentralWidget(central)

        # Root layout: horizontal split (eval bar | board+players | move list)
        rootLayout = QHBoxLayout(central)

        # --- Left: Evaluation bar ---
        self.eval_bar = EvalBarWidget()
        self.eval_bar.setFixedWidth(60)
        rootLayout.addWidget(self.eval_bar)

        # --- Center: Board + player info ---
        centerLayout = QVBoxLayout()

        # Top player (white)
        self.top_player_info = PlayerInfoWidget()
        centerLayout.addWidget(self.top_player_info, alignment=Qt.AlignmentFlag.AlignCenter)

        # Board
        self.board = BoardWidget()
        self.board.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        centerLayout.addWidget(self.board, alignment=Qt.AlignmentFlag.AlignCenter, stretch=1)

        # Bottom player (black)
        self.bottom_player_info = PlayerInfoWidget()
        centerLayout.addWidget(self.bottom_player_info, alignment=Qt.AlignmentFlag.AlignCenter)

        rootLayout.addLayout(centerLayout, stretch=3)

        # --- Right: Move list + opening name ---
        moveListLayout = QVBoxLayout()

        # Opening name
        self.opening_label = QLabel("Opening: —")
        self.opening_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opening_label.setStyleSheet("font-weight: bold; padding: 4px;")
        moveListLayout.addWidget(self.opening_label)

        # Move list
        self.move_list = MoveListWidget()
        moveListLayout.addWidget(self.move_list, stretch=1)

        rightPanel = QWidget()
        rightPanel.setLayout(moveListLayout)
        rightPanel.setFixedWidth(300)
        rootLayout.addWidget(rightPanel)
