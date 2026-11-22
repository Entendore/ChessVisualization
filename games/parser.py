import chess.polyglot

def detect_opening(board):
    """
    Detect opening name from current board position.
    Returns string or None.
    """
    try:
        with chess.polyglot.open_reader("assets/polyglot/book.bin") as reader:
            entry = reader.find(board)
            return entry.get("name", None)
    except Exception:
        return None
