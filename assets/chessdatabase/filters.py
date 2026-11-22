import re

class GameFilter:
    @staticmethod
    def by_game_type(game_type):
        return lambda g: g.get("game") == game_type

    @staticmethod
    def by_min_moves(n):
        return lambda g: len(g.get("normalized_moves", [])) >= n

    @staticmethod
    def by_player(name):
        pattern = re.compile(name, re.IGNORECASE)
        return lambda g: any(pattern.search(m["player"]) for m in g.get("normalized_moves", []))
