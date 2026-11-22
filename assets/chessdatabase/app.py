import streamlit as st
from pathlib import Path
from game_tool import GameParser, GameExporter, GameManager, GameFilter  # import from previous file
import tempfile

st.set_page_config(page_title="Chess/Shogi/Xiangqi DB Tool", layout="wide")

st.title("Chess / Shogi / Xiangqi Game Database Tool")

# ---------------- Upload Section ----------------
uploaded_files = st.file_uploader(
    "Upload game files (PGN, KIF, CSA, SFEN, ICCS, XQF, TXT)",
    type=["pgn","kif","csa","sfen","xqf","txt"],
    accept_multiple_files=True
)

# Temp folder to save uploaded files
temp_dir = Path(tempfile.mkdtemp())
uploaded_file_paths = []

# Progress for saving files
if uploaded_files:
    st.info("Saving uploaded files...")
    save_progress = st.progress(0)
    for idx, file in enumerate(uploaded_files):
        fpath = temp_dir / file.name
        with open(fpath, "wb") as f:
            f.write(file.getbuffer())
        uploaded_file_paths.append(str(fpath))
        save_progress.progress((idx + 1) / len(uploaded_files))
    st.success(f"Saved {len(uploaded_files)} files to temporary folder.")

# ---------------- Filters ----------------
st.sidebar.header("Filters")
game_type = st.sidebar.selectbox("Game Type", ["All","chess","shogi","xiangqi"])
min_moves = st.sidebar.number_input("Minimum moves", min_value=0, value=0)
player_filter = st.sidebar.text_input("Player Name (optional)")
opening_filter = st.sidebar.text_input("Opening Name (optional)")

# ---------------- Export Options ----------------
st.sidebar.header("Export Options")
export_format = st.sidebar.selectbox("Format", ["json","sqlite","csv","parquet","duckdb"])
separate = st.sidebar.checkbox("Separate DB per Game Type", value=False)

# ---------------- Process Button ----------------
if st.button("Process and Export"):

    if not uploaded_file_paths:
        st.error("Please upload at least one file!")
    else:
        parser = GameParser()
        exporter = GameExporter(temp_dir / "output")
        manager = GameManager(parser, exporter)

        # Parse games with progress bar
        st.info("Parsing games...")
        games = []
        parse_progress = st.progress(0)
        for idx, f in enumerate(uploaded_file_paths):
            try:
                g = parser.parse_file(f)
                games.append(g)
            except Exception as e:
                st.warning(f"Failed to parse {f}: {e}")
            parse_progress.progress((idx + 1) / len(uploaded_file_paths))
        st.success(f"Parsed {len(games)} games.")

        # Apply filters
        filters = []
        if game_type != "All": filters.append(GameFilter.by_game_type(game_type))
        if min_moves > 0: filters.append(GameFilter.by_min_moves(min_moves))
        if player_filter: filters.append(GameFilter.by_player(player_filter))
        if opening_filter: filters.append(GameFilter.by_opening(opening_filter))
        filtered = manager.filter_games(games, filters)
        st.info(f"{len(filtered)} games after filtering.")

        # Export with progress
        st.info("Exporting games...")
        export_progress = st.progress(0)
        total_steps = len(filtered) if filtered else 1
        for idx, g in enumerate(filtered):
            manager.export_games([g], format=export_format, separate=separate)
            export_progress.progress((idx + 1) / total_steps)
        st.success(f"Export completed! Files are in {temp_dir / 'output'}")

        # List output files
        st.subheader("Output Files")
        for f in (temp_dir / "output").iterdir():
            st.write(f.name)
            with open(f, "rb") as file_bytes:
                st.download_button(
                    label=f"Download {f.name}",
                    data=file_bytes,
                    file_name=f.name,
                    mime="application/octet-stream"
                )

# Cleanup temp folder when session ends
st.sidebar.markdown("Temporary folder will be cleared when session ends.")
