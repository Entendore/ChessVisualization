import os

def get_piece_svg(piece_name, theme="classic"):
    """
    Load SVG piece from theme folder.
    """
    base_path = os.path.join("assets", "svg_pieces", theme)
    path = os.path.join(base_path, f"{piece_name}.svg")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return None
