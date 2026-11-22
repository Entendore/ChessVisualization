import subprocess
import threading
import queue
import time

# -----------------------------
# Engine Wrapper
# -----------------------------
class Engine:
    def __init__(self, path, protocol="uci"):
        self.path = path
        self.protocol = protocol
        self.process = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        self.queue = queue.Queue()
        threading.Thread(target=self._listen, daemon=True).start()
        self._initialize_engine()

    def _listen(self):
        for line in self.process.stdout:
            self.queue.put(line.strip())

    def _send(self, command):
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def _initialize_engine(self):
        if self.protocol in ["uci", "usi"]:
            self._send(self.protocol)
            self._send("isready")
            self._wait_ready()

    def _wait_ready(self):
        while True:
            line = self.queue.get()
            if line == "readyok":
                break

    def set_position(self, fen):
        if fen.lower() == "startpos":
            self._send("position startpos")
        else:
            self._send(f"position fen " + fen)

    def go(self, movetime=1000):
        self._send(f"go movetime {movetime}")

    def get_best_move(self):
        while True:
            line = self.queue.get()
            if line.startswith("bestmove"):
                return line.split()[1]

    def get_evaluation(self):
        evals = []
        while not self.queue.empty():
            line = self.queue.get()
            if "score" in line:
                evals.append(line)
        return evals


# -----------------------------
# Game Manager
# -----------------------------
class GameManager:
    def __init__(self, engine_white, engine_black, starting_fen, game_type="chess"):
        self.engine_white = engine_white
        self.engine_black = engine_black
        self.fen = starting_fen
        self.turn = "white"
        self.game_type = game_type.lower()

        if self.game_type == "chess":
            import chess
            self.board_lib = chess
            self.board = chess.Board() if starting_fen == "startpos" else chess.Board(starting_fen)
        elif self.game_type == "shogi":
            import shogi
            self.board_lib = shogi
            self.board = shogi.Board() if starting_fen == "startpos" else shogi.Board(starting_fen)
        elif self.game_type == "xiangqi":
            import xiangqi
            self.board_lib = xiangqi
            self.board = xiangqi.Board() if starting_fen == "startpos" else xiangqi.Board(starting_fen)
        else:
            raise ValueError("Unsupported game type!")

    def make_move(self, move):
        if self.game_type == "chess":
            self.board.push_uci(move)
            return self.board.fen()
        elif self.game_type == "shogi":
            self.board.push_usi(move)
            return self.board.sfen()
        elif self.game_type == "xiangqi":
            self.board.push(move)
            return self.board.fen()

    def play_turn(self):
        current_engine = self.engine_white if self.turn == "white" else self.engine_black
        current_engine.set_position(self.fen)
        current_engine.go()
        best_move = current_engine.get_best_move()
        self.fen = self.make_move(best_move)
        evals = current_engine.get_evaluation()
        # Switch turn
        self.turn = "black" if self.turn == "white" else "white"
        return best_move, evals

    def play_game(self, max_moves=100, delay=0.1):
        print(f"Starting {self.game_type} game!")
        for move_num in range(max_moves):
            if self.board.is_game_over():
                print("Game over!")
                break
            move, evals = self.play_turn()
            print(f"[{move_num+1}] {self.turn} played {move}, evals: {evals}")
            time.sleep(delay)
        print("Game finished!")

    # -----------------------------
    # Single engine evaluation mode
    # -----------------------------
    def evaluate_position(self, engine, fen, movetime=1000):
        engine.set_position(fen)
        engine.go(movetime=movetime)
        evals = engine.get_evaluation()
        best_move = engine.get_best_move()
        return best_move, evals

