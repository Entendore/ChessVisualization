# ui/move_list_widget.py
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

import chess
import chess.pgn
import io


class MoveListWidget(QWidget):
    move_selected = pyqtSignal(int)  # emits ply index

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Two-column move list
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["#", "White", "Black"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)

        # Handle clicks
        self.table.cellClicked.connect(self._on_cell_clicked)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.moves = []  # [(white, black), ...]
        self.current_ply = -1

    # --------------------------
    # Move handling
    # --------------------------
    def add_move(self, move: str, is_white: bool = True):
        """Add a move in two-column style."""
        if is_white:
            row = self.table.rowCount()
            self.table.insertRow(row)

            move_number = row + 1
            item_number = QTableWidgetItem(str(move_number))
            item_number.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_white = QTableWidgetItem(move)
            item_white.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, item_number)
            self.table.setItem(row, 1, item_white)
            self.table.setItem(row, 2, QTableWidgetItem(""))

            self.moves.append((move, None))
        else:
            row = self.table.rowCount() - 1
            item_black = QTableWidgetItem(move)
            item_black.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_black)

            white, _ = self.moves[-1]
            self.moves[-1] = (white, move)

        self.table.scrollToBottom()
        self.set_current_ply(len(self.get_ply_list()) - 1)

    def undo_last_move(self):
        """Undo the most recent move."""
        if not self.moves:
            return

        white, black = self.moves[-1]
        if black:  # remove black
            self.table.setItem(self.table.rowCount() - 1, 2, QTableWidgetItem(""))
            self.moves[-1] = (white, None)
        else:  # remove row
            self.table.removeRow(self.table.rowCount() - 1)
            self.moves.pop()

        self.set_current_ply(len(self.get_ply_list()) - 1)

    def clear_moves(self):
        """Clear all moves."""
        self.table.setRowCount(0)
        self.moves.clear()
        self.current_ply = -1

    def get_moves(self):
        """Return moves as [(white, black), ...]."""
        return self.moves[:]

    def get_ply_list(self):
        """Flatten moves into ply-by-ply list."""
        ply_moves = []
        for white, black in self.moves:
            if white:
                ply_moves.append(white)
            if black:
                ply_moves.append(black)
        return ply_moves

    # --------------------------
    # PGN Support
    # --------------------------
    def export_pgn(self) -> str:
        """Export moves to PGN string."""
        game = chess.pgn.Game()
        node = game

        board = chess.Board()
        for move_san in self.get_ply_list():
            try:
                move = board.parse_san(move_san)
            except ValueError:
                break
            node = node.add_variation(move)
            board.push(move)

        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        return game.accept(exporter)

    def import_pgn(self, pgn_str: str):
        """Load moves from PGN string into the widget."""
        self.clear_moves()

        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if game is None:
            return

        board = game.board()
        move_number = 1
        for i, move in enumerate(game.mainline_moves()):
            san = board.san(move)
            board.push(move)
            if i % 2 == 0:  # White move
                self.add_move(san, is_white=True)
            else:           # Black move
                self.add_move(san, is_white=False)

    # --------------------------
    # Navigation & Highlighting
    # --------------------------
    def set_current_ply(self, ply: int):
        """Highlight a specific ply index."""
        if ply < -1 or ply >= len(self.get_ply_list()):
            return

        self.current_ply = ply
        if ply == -1:
            self.table.clearSelection()
            return

        row, col = divmod(ply, 2)
        col = 1 if col == 0 else 2
        self.table.setCurrentCell(row, col)
        self.table.scrollToItem(self.table.currentItem())
        self.move_selected.emit(ply)

    def _on_cell_clicked(self, row: int, col: int):
        """Handle user clicking a move."""
        if col not in (1, 2):
            return
        ply = row * 2 + (0 if col == 1 else 1)
        self.set_current_ply(ply)

    def keyPressEvent(self, event: QKeyEvent):
        """Keyboard navigation."""
        if event.key() == Qt.Key.Key_Left:
            self.set_current_ply(self.current_ply - 1)
        elif event.key() == Qt.Key.Key_Right:
            self.set_current_ply(self.current_ply + 1)
        else:
            super().keyPressEvent(event)
