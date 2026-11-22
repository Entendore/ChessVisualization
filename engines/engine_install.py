import os
import platform
import shutil
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path
import time
import importlib
import queue
import threading

# -------------------------
# Engine installation
# -------------------------
INSTALL_DIR = Path.home() / "chess_engines"
INSTALL_DIR.mkdir(exist_ok=True)

ENGINES = {
    "stockfish": {
        "url": {
            "Windows": "https://stockfishchess.org/files/stockfish-16-win-x64.zip",
            "Linux": "https://stockfishchess.org/files/stockfish-16-linux-x64.tar",
            "Darwin": "https://stockfishchess.org/files/stockfish-16-mac.zip",
        },
        "binary_name": "stockfish",
    },
    "lc0": {
        "url": {
            "Windows": "https://github.com/LeelaChessZero/lc0/releases/download/v0.30.0/lc0-v0.30.0-windows-cuda.zip",
            "Linux": "https://github.com/LeelaChessZero/lc0/releases/download/v0.30.0/lc0-v0.30.0-linux.tar.gz",
            "Darwin": "https://github.com/LeelaChessZero/lc0/releases/download/v0.30.0/lc0-v0.30.0-macos.zip",
        },
        "binary_name": "lc0",
    },
    "yaneuraou": {
        "url": {
            "Windows": "https://github.com/yaneurao/YaneuraOu/releases/download/v6.00/YaneuraOu-windows.zip",
            "Linux": "https://github.com/yaneurao/YaneuraOu/releases/download/v6.00/YaneuraOu-linux.zip",
            "Darwin": "https://github.com/yaneurao/YaneuraOu/releases/download/v6.00/YaneuraOu-mac.zip",
        },
        "binary_name": "YaneuraOu-by-gcc",
    },
    "fairy-stockfish": {
        "url": {
            "Windows": "https://github.com/fairy-stockfish/Fairy-Stockfish/releases/download/15.1.1/fairy-stockfish-15.1.1-win.zip",
            "Linux": "https://github.com/fairy-stockfish/Fairy-Stockfish/releases/download/15.1.1/fairy-stockfish-15.1.1-linux.zip",
            "Darwin": "https://github.com/fairy-stockfish/Fairy-Stockfish/releases/download/15.1.1/fairy-stockfish-15.1.1-mac.zip",
        },
        "binary_name": "fairy-stockfish",
    },
    "alpha-zero": {
        "git": "https://github.com/suragnair/alpha-zero-general.git",
        "binary_name": None,
    },
    "mu-zero": {
        "git": "https://github.com/werner-duvaud/muzero-general.git",
        "binary_name": None,
    },
}


def is_installed(engine_name: str) -> bool:
    engine = ENGINES[engine_name]
    binary_name = engine.get("binary_name")
    engine_dir = INSTALL_DIR / engine_name

    if engine_name in ["alpha-zero", "mu-zero"]:
        return engine_dir.exists()

    if binary_name:
        if shutil.which(binary_name):
            return True
        if engine_dir.exists():
            for _, _, files in os.walk(engine_dir):
                if binary_name in files or any(binary_name in f for f in files):
                    return True
    return False


def download_and_extract(engine_name: str):
    system = platform.system()
    engine = ENGINES[engine_name]
    url = engine["url"].get(system)
    if not url:
        print(f"❌ No download available for {engine_name} on {system}")
        return

    print(f"⬇️ Downloading {engine_name} from {url} ...")
    archive_path = INSTALL_DIR / f"{engine_name}.archive"
    urllib.request.urlretrieve(url, archive_path)

    engine_dir = INSTALL_DIR / engine_name
    engine_dir.mkdir(exist_ok=True)

    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(engine_dir)
    else:
        with tarfile.open(archive_path, "r:*") as tf:
            tf.extractall(engine_dir)

    archive_path.unlink()
    print(f"✅ {engine_name} installed at {engine_dir}")


def clone_and_setup(engine_name: str):
    repo_url = ENGINES[engine_name]["git"]
    target_dir = INSTALL_DIR / engine_name

    if target_dir.exists():
        print(f"✔ {engine_name} already installed")
        return

    print(f"⬇️ Cloning {engine_name} from {repo_url} ...")
    subprocess.run(["git", "clone", repo_url, str(target_dir)], check=True)

    requirements = target_dir / "requirements.txt"
    if requirements.exists():
        print(f"📦 Installing dependencies for {engine_name} ...")
        subprocess.run(
            [shutil.which("pip") or "pip3", "install", "-r", str(requirements)],
            check=True,
        )

    print(f"✅ {engine_name} installed at {target_dir}")


def install_all_engines():
    for engine in ENGINES:
        if is_installed(engine):
            print(f"✔ {engine} already installed")
        else:
            print(f"✘ {engine} not found, installing...")
            if engine in ["alpha-zero", "mu-zero"]:
                clone_and_setup(engine)
            else:
                download_and_extract(engine)


# -------------------------
# Engine wrapper
# -------------------------
class Engine:
    def __init__(self, path, protocol="uci", python_script=False):
        self.path = path
        self.protocol = protocol
        self.python_script = python_script
        self.queue = queue.Queue()
        self.process = self._start_process()
        threading.Thread(target=self._listen, daemon=True).start()
        if self.protocol in ["uci", "usi"]:
            self._initialize_engine()

    def _start_process(self):
        cmd = [self.path]
        if self.python_script:
            cmd = [shutil.which("python") or "python3", self.path]
        return subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

    def _listen(self):
        for line in self.process.stdout:
            self.queue.put(line.strip())

    def _send(self, command):
        if self.process.stdin:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()

    def _initialize_engine(self):
        self._send(self.protocol)
        self._send("isready")
        while True:
            line = self.queue.get()
            if line.strip() == "readyok":
                break

    def set_position(self, fen):
        if fen.lower() == "startpos":
            self._send("position startpos")
        else:
            self._send(f"position fen {fen}")

    def go(self, movetime=1000):
        self._send(f"go movetime {movetime}")

    def get_best_move_and_eval(self, timeout=5.0):
        evals = []
        best_move = None
        start_time = time.time()
        while True:
            try:
                line = self.queue.get(timeout=0.1)
            except queue.Empty:
                if time.time() - start_time > timeout:
                    break
                continue
            if "score" in line:
                evals.append(line)
            if line.startswith("bestmove"):
                best_move = line.split()[1]
                break
        return best_move, evals


# -------------------------
# Engine selection
# -------------------------
DEFAULT_ENGINES = {
    "chess": "stockfish",
    "shogi": "yaneuraou",
    "xiangqi": "fairy-stockfish",
}


def select_engine(game_type, custom_engine=None):
    game_type = game_type.lower()
    engine_name = custom_engine or DEFAULT_ENGINES.get(game_type)
    if not engine_name:
        raise ValueError(f"No default engine for {game_type}")
    engine_dir = INSTALL_DIR / engine_name

    # Binary search
    for root, _, files in os.walk(engine_dir):
        for f in files:
            if engine_name.lower() in f.lower() and os.access(os.path.join(root, f), os.X_OK):
                return os.path.join(root, f), "uci"

    # Python-based engines
    if engine_name in ["alpha-zero", "mu-zero"]:
        main_script = engine_dir / "main.py"
        if main_script.exists():
            return str(main_script), "python"

    raise FileNotFoundError(f"Could not find engine {engine_name} binary/script.")