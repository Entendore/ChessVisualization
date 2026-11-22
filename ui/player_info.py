# ui/player_info_widget.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class PlayerInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.white = QLabel("White: Player 1 (Rating: 2000)")
        self.black = QLabel("Black: Player 2 (Rating: 2000)")
        layout.addWidget(self.white)
        layout.addWidget(self.black)
        self.setLayout(layout)
