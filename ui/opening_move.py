# opening_widget_eco.py
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
import chess.pgn

class OpeningWidget(QWidget):
    def __init__(self, parent=None, pgn_file=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout()
        self.label = QLabel("Opening: Unknown (ECO: ???)")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.moves = []  # Moves in SAN
        self.openings_db = {}  # Move sequence -> (opening name, ECO code)

        if pgn_file:
            self.load_pgn_openings(pgn_file)

    def load_pgn_openings(self, pgn_file):
        """Load openings from a PGN file"""
        self.openings_db = {}
        with open(pgn_file) as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                moves = []
                node = game
                while node.variations:
                    node = node.variations[0]
                    moves.append(node.san())
                opening_name = game.headers.get("Opening", "Unknown")
                eco_code = game.headers.get("ECO", "???")
                self.openings_db[tuple(moves)] = (opening_name, eco_code)

    def add_move(self, move: str):
        """Add a move in SAN format and update opening"""
        self.moves.append(move)
        self.update_opening()

    def update_opening(self):
        """Match current moves against opening book incrementally"""
        best_match_name = "Unknown"
        best_match_eco = "???"
        best_match_len = 0

        for seq, (name, eco) in self.openings_db.items():
            match_len = 0
            for a, b in zip(self.moves, seq):
                if a == b:
                    match_len += 1
                else:
                    break
            if match_len > best_match_len:
                best_match_len = match_len
                best_match_name = name
                best_match_eco = eco

        self.set_opening_name(best_match_name, best_match_eco)

    def set_opening_name(self, name: str, eco: str):
        """Update label"""
        self.label.setText(f"Opening: {name} (ECO: {eco})")
