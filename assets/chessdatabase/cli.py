#!/usr/bin/env python3
import argparse
from manager import GameManager
from filters import GameFilter

def main():
    parser = argparse.ArgumentParser(description="Chess/Shogi/Xiangqi Multi-threaded Streaming with Progress")
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", default="output")
    parser.add_argument("--format", "-f", default="csv", choices=["csv","sqlite","duckdb","parquet"])
    parser.add_argument("--game", choices=["chess","shogi","xiangqi"])
    parser.add_argument("--min-moves", type=int)
    parser.add_argument("--player")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()

    manager = ThreadedGameManager(output_folder=args.output, num_threads=args.threads)

    filters = []
    if args.game: filters.append(GameFilter.by_game_type(args.game))
    if args.min_moves: filters.append(GameFilter.by_min_moves(args.min_moves))
    if args.player: filters.append(GameFilter.by_player(args.player))

    games = manager.stream_games_threaded(args.input, filters)

    if args.format == "csv":
        manager.exporter.export_csv(games)
    elif args.format == "sqlite":
        manager.exporter.export_sqlite(games)
    elif args.format == "duckdb":
        manager.exporter.export_duckdb(games)
    elif args.format == "parquet":
        manager.exporter.export_parquet(games)

if __name__ == "__main__":
    main()
