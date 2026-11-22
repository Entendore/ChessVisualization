# parsers/shogi_parser.py
import re

class ShogiParser:
    move_regex = re.compile(r"^\d+\s+(\S+)", re.MULTILINE)

    def parse_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # CSA-like: moves start with '+' or '-'
        if re.search(r"^[\+\-]\d{4}[A-Z]{2}", content, re.M):
            games_text = content.split("\n\n")  # blank lines separate games
            for game_text in games_text:
                moves = [line.strip() for line in game_text.splitlines() if line.startswith(("+","-"))]
                yield self._normalize_csa_moves(moves, filepath)
        # KIF-like
        elif re.search(r"^\d+", content, re.M):
            moves = self.move_regex.findall(content)
            yield self._normalize_kif_moves(moves, filepath)

    def _normalize_csa_moves(self, moves, filepath):
        norm = []
        for idx, move in enumerate(moves):
            norm.append({
                "move_number": idx // 2 + 1,
                "player": "black" if idx % 2 == 0 else "white",
                "notation": move,
                "from": move[1:3],
                "to": move[3:5],
                "piece": move[5:] if len(move) > 5 else None
            })
        return {"game": "shogi", "file": filepath, "normalized_moves": norm}

    def _normalize_kif_moves(self, moves, filepath):
        norm = []
        for idx, move in enumerate(moves):
            norm.append({
                "move_number": idx // 2 + 1,
                "player": "black" if idx % 2 == 0 else "white",
                "notation": move,
                "from": None,
                "to": None,
                "piece": None
            })
        return {"game": "shogi", "file": filepath, "normalized_moves": norm}
