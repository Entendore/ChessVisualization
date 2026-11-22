# ui/eval_bar_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect, pyqtProperty, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPolygon


class EvalBarWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.title = QLabel("Engine Evaluation")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.eval_label = QLabel("0.0")
        self.eval_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eval_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        layout.addWidget(self.title)
        layout.addWidget(self.eval_label)
        layout.addStretch()
        self.setLayout(layout)

        self._cp = 0             # target centipawn eval
        self._display_cp = 0     # animated displayed cp
        self.mate_score = None   # for mate display

        # animation
        self.anim = QPropertyAnimation(self, b"display_cp")
        self.anim.setDuration(500)  # ms
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    # --- Property for animation ---
    def get_display_cp(self):
        return self._display_cp

    def set_display_cp(self, value):
        self._display_cp = value
        self.update()

    display_cp = pyqtProperty(float, fget=get_display_cp, fset=set_display_cp)

    # --- API ---
    def set_eval(self, cp: float, mate: int | None = None):
        """
        Update evaluation.
        :param cp: centipawns
        :param mate: mate in N (positive = white mates, negative = black mates)
        """
        if mate is not None:
            self.mate_score = mate
            self.eval_label.setText(f"M{mate if mate > 0 else -mate}")
            self._cp = 1000 if mate > 0 else -1000
        else:
            self.mate_score = None
            self._cp = max(min(cp, 1000), -1000)
            self.eval_label.setText(f"{self._cp/100:.1f}")

        # animate smoothly from old to new cp
        self.anim.stop()
        self.anim.setStartValue(self._display_cp)
        self.anim.setEndValue(self._cp)
        self.anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # leave space at top for labels
        content_rect = QRect(0, 40, rect.width(), rect.height() - 40)

        # background (neutral dark gray)
        painter.fillRect(content_rect, QColor(50, 50, 50))

        # normalize eval → 0..1
        scaled = 0.5 + (self._display_cp / 2000.0)
        scaled = max(0.0, min(1.0, scaled))

        white_height = int(content_rect.height() * scaled)
        split_y = content_rect.top() + white_height  # marker position

        # white/green region (top)
        white_grad = QLinearGradient(0, content_rect.top(), 0, split_y)
        white_grad.setColorAt(0, QColor(230, 255, 230))   # light green
        white_grad.setColorAt(1, QColor(255, 255, 255))   # pure white
        painter.fillRect(QRect(0, content_rect.top(),
                               content_rect.width(), white_height), white_grad)

        # black/red region (bottom)
        black_grad = QLinearGradient(0, split_y, 0, content_rect.bottom())
        black_grad.setColorAt(0, QColor(30, 30, 30))      # near black
        black_grad.setColorAt(1, QColor(255, 200, 200))   # soft red
        painter.fillRect(QRect(0, split_y,
                               content_rect.width(),
                               content_rect.height() - white_height), black_grad)

        # --- Draw marker (triangle pointer) ---
        marker_size = 10
        marker_x = content_rect.right()
        marker_y = split_y

        triangle = QPolygon([
            QPoint(marker_x, marker_y - marker_size // 2),
            QPoint(marker_x, marker_y + marker_size // 2),
            QPoint(marker_x + marker_size, marker_y),
        ])

        # Dynamic marker color based on eval
        if self._display_cp > 20:
            marker_color = QColor(0, 200, 0)  # green
        elif self._display_cp < -20:
            marker_color = QColor(200, 0, 0)  # red
        else:
            marker_color = QColor(200, 200, 200)  # gray near equal

        painter.setBrush(marker_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(triangle)

        painter.end()
