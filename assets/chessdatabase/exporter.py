# exporter.py
import csv
import sqlite3
from pathlib import Path
import pandas as pd
import duckdb

class GameExporter:
    def __init__(self, output_folder="output"):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)

    # ---------- CSV ----------
    def export_csv(self, games, filename="games.csv"):
        path = self.output_folder / filename
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = None
            for g in games:
                for move in g.get("normalized_moves", []):
                    row = {"game_type": g.get("game"), "file": g.get("file"), **move}
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=row.keys())
                        writer.writeheader()
                    writer.writerow(row)
        print(f"✔ CSV exported: {path}")

    # ---------- SQLite ----------
    def export_sqlite(self, games, filename="games.sqlite"):
        path = self.output_folder / filename
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                game_type TEXT,
                file TEXT,
                move_number INTEGER,
                player TEXT,
                notation TEXT,
                piece TEXT,
                from_sq TEXT,
                to_sq TEXT
            )
        """)
        for g in games:
            gtype = g.get("game")
            file = g.get("file")
            for move in g.get("normalized_moves", []):
                cur.execute("""
                    INSERT INTO games (game_type, file, move_number, player, notation, piece, from_sq, to_sq)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (gtype, file, move["move_number"], move["player"], move["notation"],
                      move["piece"], move["from"], move["to"]))
        conn.commit()
        conn.close()
        print(f"✔ SQLite exported: {path}")
    
    # ---------- DuckDB ----------
    def export_duckdb(self, games, filename="games.duckdb"):
        path = self.output_folder / filename
        con = duckdb.connect(database=path, read_only=False)
        con.execute("DROP TABLE IF EXISTS moves")

        # Use chunks to append to DuckDB
        chunk = []
        for g in games:
            gtype = g.get("game")
            file = g.get("file")
            for move in g.get("normalized_moves", []):
                chunk.append({"game_type": gtype, "file": file, **move})
            # Insert in chunks every 1000 moves
            if len(chunk) >= 1000:
                df = pd.DataFrame(chunk)
                con.execute("INSERT INTO moves SELECT * FROM df") if con.table_exists("moves") else con.execute("CREATE TABLE moves AS SELECT * FROM df")
                chunk = []
        if chunk:
            df = pd.DataFrame(chunk)
            con.execute("INSERT INTO moves SELECT * FROM df") if con.table_exists("moves") else con.execute("CREATE TABLE moves AS SELECT * FROM df")
        con.close()
        print(f"✔ DuckDB exported: {path}")

    # ---------- Parquet ----------
    def export_parquet(self, games, filename="games.parquet"):
        path = self.output_folder / filename
        chunk = []
        for g in games:
            gtype = g.get("game")
            file = g.get("file")
            for move in g.get("normalized_moves", []):
                chunk.append({"game_type": gtype, "file": file, **move})
            if len(chunk) >= 1000:
                df = pd.DataFrame(chunk)
                df.to_parquet(path, index=False, engine="pyarrow", append=True) if path.exists() else df.to_parquet(path, index=False, engine="pyarrow")
                chunk = []
        if chunk:
            df = pd.DataFrame(chunk)
            df.to_parquet(path, index=False, engine="pyarrow", append=True) if path.exists() else df.to_parquet(path, index=False, engine="pyarrow")
        print(f"✔ Parquet exported: {path}")


