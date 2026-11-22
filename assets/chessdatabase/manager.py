# manager.py
import os
import re
from queue import Queue
from threading import Thread
from tqdm import tqdm
from parsers.chess_parser import ChessParser
from parsers.shogi_parser import ShogiParser
from parsers.xiangqi_parser import XiangqiParser
from exporter import GameExporter
from filters import GameFilter
from logger import setup_logger

class GameManager:
    def __init__(self, output_folder="output", num_threads=4):
        self.parsers = {
            "chess": ChessParser(),
            "shogi": ShogiParser(),
            "xiangqi": XiangqiParser()
        }
        self.exporter = GameExporter(output_folder)
        self.num_threads = num_threads
        self.logger = setup_logger()

    def _detect_game_type(self, filepath):
        ext = filepath.lower().split(".")[-1]
        if ext in ["pgn"]: return "chess"
        elif ext in ["csa","kif","sfen","ki2"]: return "shogi"
        elif ext in ["xqf","iccs","txt"]: return "xiangqi"
        else:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read(1024)
                if re.search(r"\[Event.*\]", content): return "chess"
                elif re.search(r"^[\+\-]\d{4}[A-Z]{2}", content, re.M) or re.search(r"^\d+", content, re.M): return "shogi"
                elif re.search(r"[a-i][0-9]-[a-i][0-9]", content, re.I) or re.search(r"\d+\.", content): return "xiangqi"
            except Exception as e:
                self.logger.error(f"Failed to read {filepath}: {e}")
        return None

    def stream_games_threaded(self, folder, filters=None):
        file_queue = Queue()
        output_queue = Queue()
        all_files = []

        # Collect all files
        for root, _, files in os.walk(folder):
            for fname in files:
                fpath = os.path.join(root, fname)
                all_files.append(fpath)
                file_queue.put(fpath)

        total_files = len(all_files)
        pbar = tqdm(total=total_files, desc="Processing files")

        def worker():
            while not file_queue.empty():
                fpath = file_queue.get()
                try:
                    game_type = self._detect_game_type(fpath)
                    if game_type and game_type in self.parsers:
                        parser = self.parsers[game_type]
                        for game in parser.parse_file(fpath):
                            if not filters or all(f(game) for f in filters):
                                output_queue.put(game)
                    else:
                        output_queue.put({"game": "unknown", "file": fpath})
                except Exception as e:
                    self.logger.error(f"Error processing {fpath}: {e}")
                finally:
                    file_queue.task_done()
                    pbar.update(1)

        threads = []
        for _ in range(self.num_threads):
            t = Thread(target=worker)
            t.start()
            threads.append(t)

        while any(t.is_alive() for t in threads) or not output_queue.empty():
            while not output_queue.empty():
                yield output_queue.get()

        for t in threads:
            t.join()
        pbar.close()
        self.logger.info("All files processed.")
