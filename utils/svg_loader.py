import os

class SVGPieceLoader:
    """
    Loads SVG pieces from assets/svg_pieces with support for multiple themes.
    """

    def __init__(self, theme="classic"):
        """
        Initialize the loader with a theme.
        :param theme: Folder name inside assets/svg_pieces containing SVG files.
        """
        self.theme = theme
        self.base_path = os.path.join("assets", "svg_pieces", self.theme)
        if not os.path.exists(self.base_path):
            raise FileNotFoundError(f"SVG theme folder not found: {self.base_path}")

        # Cache loaded SVGs
        self.cache = {}

    def load_piece(self, piece_name):
        """
        Load an SVG for the given piece name (e.g., 'wP', 'bK').
        :param piece_name: string representing piece, e.g., 'wP' = white pawn
        :return: SVG content as string
        """
        if piece_name in self.cache:
            return self.cache[piece_name]

        file_path = os.path.join(self.base_path, f"{piece_name}.svg")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SVG piece not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        self.cache[piece_name] = svg_content
        return svg_content

    def set_theme(self, theme):
        """
        Change the theme dynamically.
        """
        self.theme = theme
        self.base_path = os.path.join("assets", "svg_pieces", self.theme)
        if not os.path.exists(self.base_path):
            raise FileNotFoundError(f"SVG theme folder not found: {self.base_path}")
        self.cache = {}  # Clear cache
