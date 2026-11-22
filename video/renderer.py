from moviepy.editor import ImageSequenceClip
import chess
from games.parsers import detect_opening

class VideoRenderer:
    """
    Generates MP4 video with animated moves, evaluation bar, move list, and opening name.
    """
    def __init__(self, config, engines=None):
        self.config = config
        from visualization.board import BoardRenderer
        self.board_renderer = BoardRenderer(config)
        self.engines = engines  # List of EngineManager for side-by-side comparison

    def render_game_video(self, game, evaluations_list):
        """
        evaluations_list: list of evaluations from one or more engines
        """
        board = chess.Board()
        frames = []
        prev_evals = [0] * len(evaluations_list)
        move_history = []

        # Detect opening at start
        opening_name = detect_opening(board)

        for idx, move_uci in enumerate(game["moves"]):
            move = chess.Move.from_uci(move_uci)
            board.push(move)
            move_history.append(move_uci)

            # Interpolate evaluation for one or multiple engines
            current_evals = [evals[idx] for evals in evaluations_list]
            # For side-by-side, we could split board or overlay colors

            # Render animated frames
            move_frames = self.board_renderer.render_animated_move(
                board, move, move_history, prev_evals[0], current_evals[0], opening_name
            )
            frames.extend(move_frames)
            prev_evals = current_evals

        clip = ImageSequenceClip([frame for frame in frames], fps=self.config.video_fps)
        clip.write_videofile(self.config.video_output_path, codec="libx264")
