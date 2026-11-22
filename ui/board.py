# ui/board.py
from PyQt6.QtWidgets import QFrame
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRect, QSize

class BoardWidget(QFrame):
    def __init__(self, game_type="chess", parent=None):
        super().__init__(parent)
        self.game_type = game_type.lower()
        self.setFixedSize(480, 480)

        # Game-specific dimensions
        if self.game_type == "chess":
            self.rows, self.cols = 8, 8
            self.light_color = QColor("#F0D9B5")
            self.dark_color = QColor("#B58863")
            # Use standard Unicode chess symbols
            self.default_board_state()
        elif self.game_type == "shogi":
            self.rows, self.cols = 9, 9
            self.light_color = QColor("#F5DEB3")
            self.dark_color = QColor("#F5DEB3")
            self.default_board_state()
        elif self.game_type == "xiangqi":
            self.rows, self.cols = 10, 9
            self.light_color = QColor("#FFE4C4")
            self.dark_color = QColor("#FFE4C4")
            self.default_board_state()
        else:
            raise ValueError("Unsupported game type")

        self.highlight_color = QColor(255, 255, 0, 100)
        self.last_move = None
        self.selected_square = None

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)

    def default_board_state(self):
        """Initialize pieces for chess, shogi, or xiangqi"""
        self.board_state = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        if self.game_type == "chess":
            # Chess pieces (Unicode)
            back_rank = ["♖","♘","♗","♕","♔","♗","♘","♖"]
            pawns = ["♙"]*8
            self.board_state[0] = [p.lower() for p in back_rank]  # black
            self.board_state[1] = ["♟"]*8
            self.board_state[6] = ["♙"]*8
            self.board_state[7] = back_rank  # white
        elif self.game_type == "shogi":
            # Simple text abbreviations for Shogi pieces
            pieces = ["L","N","S","G","K","G","S","N","L"]
            self.board_state[0] = [p.lower() for p in pieces]  # top player
            self.board_state[1] = ["B","R"] + [""]*7  # Bishops/Rooks simplified
            self.board_state[2] = ["P"]*9
            self.board_state[6] = ["p"]*9
            self.board_state[7] = ["b","r"] + [""]*7
            self.board_state[8] = pieces  # bottom player
        elif self.game_type == "xiangqi":
            # Xiangqi symbols (Chinese characters)
            # Top player
            self.board_state[0] = ["車","馬","相","仕","將","仕","相","馬","車"]
            self.board_state[2] = ["砲",""]*5 + ["砲",""]*4
            self.board_state[3] = ["卒"]*9
            # Bottom player
            self.board_state[9] = ["車","馬","象","士","帥","士","象","馬","車"]
            self.board_state[7] = ["炮",""]*5 + ["炮",""]*4
            self.board_state[6] = ["兵"]*9

    def minimumSizeHint(self):
        return QSize(400, 400)

    def paintEvent(self, event):
        painter = QPainter(self)
        size = min(self.width(), self.height())
        square_width = self.width() / self.cols
        square_height = self.height() / self.rows

        # Draw the board
        for row in range(self.rows):
            for col in range(self.cols):
                rect = QRect(
                    int(col * square_width),
                    int(row * square_height),
                    int(square_width),
                    int(square_height)
                )

                # Chess: alternating colors; others: plain
                if self.game_type == "chess":
                    color = self.light_color if (row + col) % 2 == 0 else self.dark_color
                    painter.fillRect(rect, color)
                else:
                    painter.fillRect(rect, self.light_color)
                    # Draw grid
                    painter.setPen(QPen(Qt.GlobalColor.black, 1))
                    painter.drawRect(rect)

                # Draw piece if any
                piece = self.board_state[row][col]
                if piece:
                    painter.setPen(Qt.GlobalColor.black)
                    font = QFont("Arial", int(square_height * 0.6))
                    font.setBold(True)
                    painter.setFont(font)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, piece)

        # Draw last move highlight
        if self.last_move:
            for sq in self.last_move:
                row, col = sq
                painter.fillRect(
                    int(col*square_width),
                    int(row*square_height),
                    int(square_width),
                    int(square_height),
                    self.highlight_color
                )

        # Draw selected square highlight
        if self.selected_square:
            row, col = self.selected_square
            painter.setPen(QPen(QColor("blue"), 3))
            painter.drawRect(
                int(col * square_width),
                int(row * square_height),
                int(square_width),
                int(square_height)
            )
