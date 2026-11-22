# parsers/xiangqi_parser.py
import re

class XiangqiParser:
    def parse_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        # ICCS (a0-b0)
        if re.search(r"[a-i][0-9]-[a-i][0-9]", text, re.I):
            moves = [m for m in text.split() if "-" in m]
            yield self._normalize_moves(moves, filepath)
        # PGN-like
        elif re.search(r"\d+\.", text):
            moves = re.sub(r"\d+\.", "", text).split()
            yield self._normalize_moves(moves, filepath)

    def _normalize_moves(self, moves, filepath):
        norm = []
        for idx, move in enumerate(moves):
            from_sq, to_sq = None, None
            if "-" in move and len(move) == 5:
                from_sq, to_sq = move.split("-")
            norm.append({
                "move_number": idx // 2 + 1,
                "player": "red" if idx % 2 == 0 else "black",
                "notation": move,
                "from": from_sq,
                "to": to_sq,
                "piece": None
            })
