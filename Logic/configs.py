import os

# Create folder for generated Python classes
os.makedirs("game_classes", exist_ok=True)

# Define the game variants and their rules
game_variants = {
    "chess": {
        "board_size": [8, 8],
        "pieces": {
            "king": "one square any direction",
            "queen": "any direction any number",
            "rook": "horizontal or vertical any number",
            "bishop": "diagonal any number",
            "knight": "L-shape",
            "pawn": "forward 1, attack diagonal"
        },
        "special_rules": ["castling", "en_passant", "pawn_promotion"]
    },
    "shogi": {
        "board_size": [9, 9],
        "pieces": {
            "king": "one square any direction",
            "gold_general": "one square forward/side/back-diagonal",
            "silver_general": "one square forward or diagonal",
            "knight": "jump 2 forward 1 sideways",
            "lance": "any number forward",
            "bishop": "diagonal any number",
            "rook": "horizontal or vertical any number",
            "pawn": "forward 1"
        },
        "special_rules": ["drop_pieces", "promotion_zone"]
    },
    "xiangqi": {
        "board_size": [9, 10],
        "pieces": {
            "general": "one square within palace",
            "advisor": "one square diagonal within palace",
            "elephant": "two squares diagonal, cannot cross river",
            "horse": "L-shape, blocked if adjacent blocked",
            "chariot": "horizontal or vertical any number",
            "cannon": "like chariot, jumps to capture",
            "soldier": "forward 1, sideways after river"
        },
        "special_rules": ["river", "palace"]
    }
}

# Generate Python class file for each variant
for variant, rules in game_variants.items():
    class_name = variant.capitalize()
    file_path = os.path.join("game_classes", f"{variant}.py")
    with open(file_path, "w") as f:
        f.write(f"class {class_name}:\n")
        f.write(f"    def __init__(self):\n")
        f.write(f"        self.name = '{variant}'\n")
        f.write(f"        self.board_size = {rules['board_size']}\n")
        f.write(f"        self.pieces = {rules['pieces']}\n")
        f.write(f"        self.special_rules = {rules['special_rules']}\n\n")
        
        f.write(f"    def get_piece_moves(self, piece_name):\n")
        f.write(f"        return self.pieces.get(piece_name, 'Unknown piece')\n\n")
        
        f.write(f"    def display_info(self):\n")
        f.write(f"        print(f\"Game: {self.name}\")\n")
        f.write(f"        print(f\"Board size: {self.board_size}\")\n")
        f.write(f"        print(f\"Pieces and moves: {self.pieces}\")\n")
        f.write(f"        print(f\"Special rules: {self.special_rules}\")\n")
        
    print(f"Python class file '{file_path}' generated successfully!")
