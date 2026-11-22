# parsers/chess_parser.py
import re

class ChessParser:
    move_regex = re.compile(r"(\d+)\.(\s*[^ \n]+)\s*([^ \n]*)?")

    def parse_file(self, filepath):
        headers = {}
        moves_text = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("[") and "]" in line:
                    key, val = line[1:-1].split(" ", 1)
                    headers[key] = val.strip('"')
                elif line == "":
                    if moves_text:
                        yield self._parse_moves(" ".join(moves_text), filepath, headers)
                        headers = {}
                        moves_text = []
                else:
                    moves_text.append(line)
            if moves_text:
                yield self._parse_moves(" ".join(moves_text), filepath, headers)

    def _parse_moves(self, moves_str, filepath, headers):
        moves = []
        for match in self.move_regex.finditer(moves_str):
            move_number = int(match.group(1))
            white = match.group(2)
            black = match.group(3) if match.group(3) else None
            moves.append({"move_number": move_number, "player": "white", "notation": white, "from": None, "to": None, "piece": None})
            if black:
                moves.append({"move_number": move_number, "player": "black", "notation": black, "from": None, "to": None, "piece": None})
        return {"game": "chess", "file": filepath, "headers": headers, "normalized_moves": moves}
