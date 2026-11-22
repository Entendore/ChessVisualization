#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/chess_engines"
mkdir -p "$INSTALL_DIR"

# Engines and sources
declare -A STOCKFISH_URL=(
  ["Linux"]="https://stockfishchess.org/files/stockfish-16-linux-x64.tar"
  ["Darwin"]="https://stockfishchess.org/files/stockfish-16-mac.zip"
  ["Windows"]="https://stockfishchess.org/files/stockfish-16-win-x64.zip"
)
declare -A LC0_URL=(
  ["Linux"]="https://github.com/LeelaChessZero/lc0/releases/download/v0.30.0/lc0-v0.30.0-linux.tar.gz"
  ["Darwin"]="https://github.com/LeelaChessZero/lc0/releases/download/v0.30.0/lc0-v0.30.0-macos.zip"
  ["Windows"]="https://github.com/LeelaChessZero/lc0/releases/download/v0.30.0/lc0-v0.30.0-windows-cuda.zip"
)
declare -A YANEURAOU_URL=(
  ["Linux"]="https://github.com/yaneurao/YaneuraOu/releases/download/v6.00/YaneuraOu-linux.zip"
  ["Darwin"]="https://github.com/yaneurao/YaneuraOu/releases/download/v6.00/YaneuraOu-mac.zip"
  ["Windows"]="https://github.com/yaneurao/YaneuraOu/releases/download/v6.00/YaneuraOu-windows.zip"
)
declare -A FAIRY_URL=(
  ["Linux"]="https://github.com/fairy-stockfish/Fairy-Stockfish/releases/download/15.1.1/fairy-stockfish-15.1.1-linux.zip"
  ["Darwin"]="https://github.com/fairy-stockfish/Fairy-Stockfish/releases/download/15.1.1/fairy-stockfish-15.1.1-mac.zip"
  ["Windows"]="https://github.com/fairy-stockfish/Fairy-Stockfish/releases/download/15.1.1/fairy-stockfish-15.1.1-win.zip"
)
ALPHAZERO_GIT="https://github.com/suragnair/alpha-zero-general.git"
MUZERO_GIT="https://github.com/werner-duvaud/muzero-general.git"

OS=$(uname -s)

download_and_extract() {
  local name=$1
  local url=$2
  local target="$INSTALL_DIR/$name"
  mkdir -p "$target"

  echo "Downloading $name..."
  tmpfile=$(mktemp)
  curl -L "$url" -o "$tmpfile"

  if [[ "$url" == *.zip ]]; then
    unzip -q "$tmpfile" -d "$target"
  else
    tar -xf "$tmpfile" -C "$target"
  fi

  rm "$tmpfile"
  echo "Installed $name into $target"
}

install_alpha_zero() {
  local target="$INSTALL_DIR/alpha-zero-general"
  if [[ -d "$target" ]]; then
    echo "✔ AlphaZero already installed"
    return
  fi
  echo "Cloning AlphaZero-General..."
  git clone "$ALPHAZERO_GIT" "$target"
  echo "Installing Python dependencies..."
  pip install -r "$target/requirements.txt"
}

install_muzero() {
  local target="$INSTALL_DIR/muzero-general"
  if [[ -d "$target" ]]; then
    echo "✔ MuZero already installed"
    return
  fi
  echo "Cloning MuZero-General..."
  git clone "$MUZERO_GIT" "$target"
  echo "Installing Python dependencies..."
  pip install -r "$target/requirements.txt"
}

# === MAIN ===
echo "Installing engines into $INSTALL_DIR"

# Stockfish
if command -v stockfish >/dev/null || [[ -d "$INSTALL_DIR/stockfish" ]]; then
  echo "✔ Stockfish already installed"
else
  download_and_extract "stockfish" "${STOCKFISH_URL[$OS]}"
fi

# Lc0
if command -v lc0 >/dev/null || [[ -d "$INSTALL_DIR/lc0" ]]; then
  echo "✔ Lc0 already installed"
else
  download_and_extract "lc0" "${LC0_URL[$OS]}"
fi

# YaneuraOu (Shogi)
if [[ -d "$INSTALL_DIR/yaneuraou" ]]; then
  echo "✔ YaneuraOu already installed"
else
  download_and_extract "yaneuraou" "${YANEURAOU_URL[$OS]}"
fi

# Fairy-Stockfish (Xiangqi)
if [[ -d "$INSTALL_DIR/fairy-stockfish" ]]; then
  echo "✔ Fairy-Stockfish already installed"
else
  download_and_extract "fairy-stockfish" "${FAIRY_URL[$OS]}"
fi

# AlphaZero
install_alpha_zero

# MuZero
install_muzero

echo "✅ All engines installed successfully."
