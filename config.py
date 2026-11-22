class Config:
    def __init__(self):
        self.game_type = "chess"
        self.game_files = ["games/sample.pgn"]
        self.engine_choice = "stockfish"
        self.engine_path = "stockfish"  # Path to Stockfish binary

        # Visualization
        self.board_theme = "classic"
        self.piece_style = "unicode"
        self.highlight_last_move = True

        # Video
        self.video_output_path = "output/game.mp4"
        self.video_resolution = (640, 640)
        self.video_fps = 2  # For demo, slow enough to see each move
        self.animation_speed = 1.0
