import os
import re
import argparse

# ----------------------------
# Layouts
# ----------------------------
LAYOUTS = {
    "default": {"piece_size": 80, "margin": 15, "cols": 10, "label_height": 20},
    "compact": {"piece_size": 50, "margin": 8, "cols": 12, "label_height": 15},
    "poster": {"piece_size": 120, "margin": 25, "cols": 8, "label_height": 30}
}

# ----------------------------
# Themes with fill, text, and border colors
# ----------------------------
themes = {
    "classic": {
        "base_colors": {
            "chess_white_piece": "#ffffff",
            "chess_black_piece": "#000000",
            "xiangqi_red_piece": "#ff0000",
            "xiangqi_black_piece": "#000000",
            "shogi_light_piece": "#ffffff",
            "shogi_dark_piece": "#000000"
        },
        "text_colors": {
            "chess": {"white": "#808080", "black": "#808080"},
            "shogi": {"light": "#aaaaaa", "dark": "#aaaaaa"},
            "xiangqi": {"red": "#aa0000", "black": "#555555"}
        },
        "border_colors": {
            "chess": {"white": "#000000", "black": "#ffffff"},
            "shogi": {"light": "#aaaaaa", "dark": "#aaaaaa"},
            "xiangqi": {"red": "#880000", "black": "#222222"}
        },
        "promotion_highlight": "#fff0b3"
    },
    "pastel": {
        "base_colors": {
            "chess_white_piece": "#fffbf0",
            "chess_black_piece": "#a0a0a0",
            "xiangqi_red_piece": "#ffcccc",
            "xiangqi_black_piece": "#808080",
            "shogi_light_piece": "#fff5cc",
            "shogi_dark_piece": "#d1c0a0"
        },
        "text_colors": {
            "chess": {"white": "#333333", "black": "#111111"},
            "shogi": {"light": "#dddddd", "dark": "#666666"},
            "xiangqi": {"red": "#cc6666", "black": "#444444"}
        },
        "border_colors": {
            "chess": {"white": "#999999", "black": "#555555"},
            "shogi": {"light": "#999999", "dark": "#555555"},
            "xiangqi": {"red": "#cc4444", "black": "#222222"}
        },
        "promotion_highlight": "#ffe5b3"
    },
    "dark_mode": {
        "base_colors": {
            "chess_white_piece": "#222222",
            "chess_black_piece": "#000000",
            "xiangqi_red_piece": "#880000",
            "xiangqi_black_piece": "#222222",
            "shogi_light_piece": "#444444",
            "shogi_dark_piece": "#222222"
        },
        "text_colors": {
            "chess": {"white": "#eeeeee", "black": "#cccccc"},
            "shogi": {"light": "#999999", "dark": "#bbbbbb"},
            "xiangqi": {"red": "#ff6666", "black": "#aaaaaa"}
        },
        "border_colors": {
            "chess": {"white": "#cccccc", "black": "#eeeeee"},
            "shogi": {"light": "#bbbbbb", "dark": "#999999"},
            "xiangqi": {"red": "#ff4444", "black": "#aaaaaa"}
        },
        "promotion_highlight": "#ffcc88"
    }
}

# ----------------------------
# Piece Definitions
# ----------------------------
pieces = {
    "chess": {"King": "♔", "Queen": "♕", "Rook": "♖", "Bishop": "♗", "Knight": "♘", "Pawn": "♙"},
    "shogi": {
        "King": "王", "Rook": "飛", "Bishop": "角", "GoldGeneral": "金",
        "SilverGeneral": "銀", "Knight": "桂", "Lance": "香", "Pawn": "歩",
        "PromotedRook": "龍", "PromotedBishop": "馬", "PromotedSilver": "成銀",
        "PromotedKnight": "成桂", "PromotedLance": "成香", "PromotedPawn": "と"
    },
    "xiangqi": {
        "General": "將", "Advisor": "士", "Elephant": "象", "Horse": "馬",
        "Chariot": "車", "Cannon": "砲", "Soldier": "卒"
    }
}

# ----------------------------
# Mapping descriptive color keys
# ----------------------------
PIECE_COLOR_KEYS = {
    "chess": {"white": "chess_white_piece", "black": "chess_black_piece"},
    "shogi": {"white": "shogi_light_piece", "black": "shogi_dark_piece"},
    "xiangqi": {"red": "xiangqi_red_piece", "black": "xiangqi_black_piece"}
}

SHOGI_TEXT_KEYS = {"white": "light", "black": "dark"}
XIANGQI_TEXT_KEYS = {"red": "red", "black": "black"}

# ----------------------------
# SVG generation functions
# ----------------------------
def create_chess_svg(symbol, fill_color, text_color, border_color, size=100):
    font_size = size * 0.6
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
  <rect x="0" y="0" width="{size}" height="{size}" rx="{size*0.15}" ry="{size*0.15}" fill="{fill_color}" stroke="{border_color}" stroke-width="4"/>
  <text x="50%" y="55%" font-size="{font_size}" text-anchor="middle" fill="{text_color}" font-family="Arial" dominant-baseline="middle">{symbol}</text>
</svg>'''

def create_shogi_svg(symbol, fill_color, text_color, border_color, promoted=False, size=100, highlight_color="#fff0b3"):
    points = [(size*0.5, 5), (size-5, size*0.3), (size-15, size-5), (15, size-5), (5, size*0.3)]
    points_str = " ".join(f"{x},{y}" for x, y in points)
    font_size = size / max(2.5, len(symbol) * 0.8)
    
    if promoted:
        highlight_svg = f'<polygon points="{points_str}" fill="{highlight_color}" stroke="{border_color}" stroke-width="4"/>'
        vertical_symbol = ''.join(f'<tspan x="50%" dy="{font_size}">{c}</tspan>' for c in symbol)
        text_svg = f'<text x="50%" y="{size/4}" font-size="{font_size}" text-anchor="middle" fill="{text_color}" font-family="MS Gothic, Arial">{vertical_symbol}</text>'
    else:
        highlight_svg = f'<polygon points="{points_str}" fill="{fill_color}" stroke="{border_color}" stroke-width="4"/>'
        text_svg = f'<text x="50%" y="55%" font-size="{font_size}" text-anchor="middle" fill="{text_color}" font-family="MS Gothic, Arial" dominant-baseline="middle">{symbol}</text>'
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
  {highlight_svg}
  {text_svg}
</svg>'''

def create_xiangqi_svg(symbol, fill_color, text_color, border_color, size=100):
    font_size = size / max(1.8, len(symbol) * 0.9)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
  <circle cx="{size/2}" cy="{size/2}" r="{size/2 - 5}" fill="{fill_color}" stroke="{border_color}" stroke-width="4"/>
  <text x="50%" y="55%" font-size="{font_size}" text-anchor="middle" fill="{text_color}" font-family="SimSun, Arial" dominant-baseline="middle">{symbol}</text>
</svg>'''

# ----------------------------
# Preview generation
# ----------------------------
def generate_preview(piece_svgs, preview_file, text_colors, piece_size, margin, cols, label_height):
    rows = (len(piece_svgs) + cols - 1) // cols
    width = cols * (piece_size + margin) + margin
    height = rows * (piece_size + margin + label_height) + margin

    svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">\n'
    x, y = margin, margin

    for idx, (svg_str, piece_name, game, player) in enumerate(piece_svgs):
        inner_svg = svg_str.split(">", 1)[1].rsplit("</svg>", 1)[0]
        if game == "shogi":
            text_color = text_colors["shogi"][SHOGI_TEXT_KEYS[player]]
        elif game == "xiangqi":
            text_color = text_colors["xiangqi"][XIANGQI_TEXT_KEYS[player]]
        else:
            text_color = text_colors[game][player]

        inner_svg = re.sub(r'(<text[^>]*?)fill="[^"]+"', rf'\1fill="{text_color}"', inner_svg)
        svg_content += f'<g transform="translate({x},{y})">{inner_svg}</g>\n'
        svg_content += f'<text x="{x + piece_size/2}" y="{y + piece_size + label_height*0.7}" text-anchor="middle" font-family="Arial" font-size="12" fill="black">{piece_name}</text>\n'

        x += piece_size + margin
        if (idx + 1) % cols == 0:
            x = margin
            y += piece_size + margin + label_height

    svg_content += '</svg>'
    with open(preview_file, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Preview sheet generated: {preview_file}")

# ----------------------------
# CLI
# ----------------------------
parser = argparse.ArgumentParser(description="Generate chess, shogi, xiangqi pieces with descriptive themes.")
parser.add_argument("--theme", type=str, default="classic", choices=themes.keys())
parser.add_argument("--layout", type=str, default="default", choices=LAYOUTS.keys())
parser.add_argument("--output", type=str, default="svg_pieces")
parser.add_argument("--batch", action="store_true")

# Dynamically add override args
games_players = {
    "chess": ["white","black"],
    "shogi": ["white","black"],
    "xiangqi": ["red","black"]
}
for game, players in games_players.items():
    for player in players:
        for key_type in ["fill","text","border"]:
            parser.add_argument(f"--{game}-{player}-{key_type}", type=str, help=f"Override {key_type} color for {game} {player} pieces")

args = parser.parse_args()

# ----------------------------
# Generation loop
# ----------------------------
themes_to_generate = themes.keys() if args.batch else [args.theme]
layouts_to_generate = LAYOUTS.keys() if args.batch else [args.layout]

for theme_name in themes_to_generate:
    theme_data = themes[theme_name]
    base_colors = theme_data["base_colors"].copy()
    text_colors = theme_data["text_colors"].copy()
    border_colors = theme_data["border_colors"].copy()
    highlight_color = theme_data.get("promotion_highlight", "#fff0b3")

    # Apply CLI overrides
    for game, players in games_players.items():
        for player in players:
            for key_type in ["fill","text","border"]:
                cli_value = getattr(args, f"{game}_{player}_{key_type}")
                if cli_value:
                    if key_type == "fill":
                        base_colors[PIECE_COLOR_KEYS[game][player]] = cli_value
                    elif key_type == "text":
                        if game == "shogi":
                            text_colors["shogi"][SHOGI_TEXT_KEYS[player]] = cli_value
                        elif game == "xiangqi":
                            text_colors["xiangqi"][XIANGQI_TEXT_KEYS[player]] = cli_value
                        else:
                            text_colors[game][player] = cli_value
                    elif key_type == "border":
                        if game == "shogi":
                            border_colors["shogi"][SHOGI_TEXT_KEYS[player]] = cli_value
                        elif game == "xiangqi":
                            border_colors["xiangqi"][XIANGQI_TEXT_KEYS[player]] = cli_value
                        else:
                            border_colors[game][player] = cli_value

    for layout_name in layouts_to_generate:
        layout = LAYOUTS[layout_name]
        piece_size = layout["piece_size"]
        margin = layout["margin"]
        cols = layout["cols"]
        label_height = layout["label_height"]

        print(f"\nGenerating theme '{theme_name}' with layout '{layout_name}'")
        theme_dir = os.path.join(args.output, f"{theme_name}_{layout_name}")
        os.makedirs(theme_dir, exist_ok=True)

        piece_svgs_combined = []

        for game, piece_map in pieces.items():
            game_dir = os.path.join(theme_dir, game)
            os.makedirs(game_dir, exist_ok=True)

            players = games_players[game]

            for piece_name, symbol in piece_map.items():
                for player in players:
                    fill_color = base_colors[PIECE_COLOR_KEYS[game][player]]
                    text_color = (text_colors["shogi"][SHOGI_TEXT_KEYS[player]] if game=="shogi"
                                  else text_colors["xiangqi"][XIANGQI_TEXT_KEYS[player]] if game=="xiangqi"
                                  else text_colors[game][player])
                    border_color = (border_colors["shogi"][SHOGI_TEXT_KEYS[player]] if game=="shogi"
                                    else border_colors["xiangqi"][XIANGQI_TEXT_KEYS[player]] if game=="xiangqi"
                                    else border_colors[game][player])

                    if game == "shogi":
                        promoted = piece_name.startswith("Promoted")
                        svg_str = create_shogi_svg(symbol, fill_color, text_color, border_color, promoted, piece_size, highlight_color)
                    elif game == "chess":
                        svg_str = create_chess_svg(symbol, fill_color, text_color, border_color, piece_size)
                    else:
                        svg_str = create_xiangqi_svg(symbol, fill_color, text_color, border_color, piece_size)

                    path_svg = os.path.join(game_dir, f"{piece_name}_{player}.svg")
                    with open(path_svg, "w", encoding="utf-8") as f:
                        f.write(svg_str)

                    piece_svgs_combined.append((svg_str, piece_name, game, player))

        # Combined preview
        preview_svg = os.path.join(theme_dir, "preview_sheet_labeled.svg")
        generate_preview(piece_svgs_combined, preview_svg, text_colors, piece_size, margin, cols, label_height)

        # Per-game previews
        for game in pieces.keys():
            game_svgs = [item for item in piece_svgs_combined if item[2] == game]
            game_preview_svg = os.path.join(theme_dir, f"preview_{game}.svg")
            generate_preview(game_svgs, game_preview_svg, text_colors, piece_size, margin, cols, label_height)
