"""Generate visual assets for the Enterprise-HAN-Agent README.

The script intentionally uses Pillow only, so it can run in lightweight local
environments without Graphviz, Mermaid CLI, or browser rendering.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"

CANVAS = (1400, 900)
BG = "#f7f9fc"
INK = "#1f2937"
MUTED = "#64748b"
GRID = "#d8dee9"
BLUE = "#2563eb"
GREEN = "#059669"
AMBER = "#d97706"
RED = "#dc2626"
PURPLE = "#7c3aed"
CYAN = "#0891b2"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT_TITLE = font(42, True)
FONT_SUBTITLE = font(24)
FONT_LABEL = font(24, True)
FONT_SMALL = font(19)
FONT_TINY = font(16)


def canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", CANVAS, BG)
    draw = ImageDraw.Draw(image)
    for x in range(0, CANVAS[0], 80):
        draw.line((x, 0, x, CANVAS[1]), fill=GRID, width=1)
    for y in range(0, CANVAS[1], 80):
        draw.line((0, y, CANVAS[0], y), fill=GRID, width=1)
    draw.rectangle((0, 0, CANVAS[0], 118), fill="#ffffff")
    draw.text((72, 30), title, fill=INK, font=FONT_TITLE)
    draw.text((74, 82), subtitle, fill=MUTED, font=FONT_SUBTITLE)
    return image, draw


def rounded_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill: str,
    outline: str,
    title: str,
    body: str = "",
    title_fill: str = "#ffffff",
) -> None:
    draw.rounded_rectangle(xy, radius=22, fill=fill, outline=outline, width=3)
    x1, y1, x2, y2 = xy
    draw.text((x1 + 24, y1 + 24), title, fill=title_fill, font=FONT_LABEL)
    if body:
        draw.text((x1 + 24, y1 + 66), body, fill=title_fill, font=FONT_SMALL, spacing=6)


def node(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int, fill: str, title: str, subtitle: str) -> None:
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline="#ffffff", width=5)
    tw = draw.textbbox((0, 0), title, font=FONT_LABEL)[2]
    sw = draw.textbbox((0, 0), subtitle, font=FONT_TINY)[2]
    draw.text((x - tw / 2, y - 18), title, fill="#ffffff", font=FONT_LABEL)
    draw.text((x - sw / 2, y + 18), subtitle, fill="#eef2ff", font=FONT_TINY)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str, width: int = 5) -> None:
    draw.line((*start, *end), fill=color, width=width)
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    size = 18
    tip = (ex, ey)
    left = (ex - ux * size + px * size * 0.55, ey - uy * size + py * size * 0.55)
    right = (ex - ux * size - px * size * 0.55, ey - uy * size - py * size * 0.55)
    draw.polygon([tip, left, right], fill=color)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str = INK) -> None:
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=FONT_SMALL)
    draw.rounded_rectangle((bbox[0] - 12, bbox[1] - 8, bbox[2] + 12, bbox[3] + 8), radius=12, fill="#ffffff", outline="#cbd5e1")
    draw.text((x, y), text, fill=color, font=FONT_SMALL)


def save(image: Image.Image, filename: str) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    image.save(ASSET_DIR / filename, quality=95)


def draw_metapath() -> None:
    image, draw = canvas(
        "HAN Meta-path Attention",
        "Heterogeneous graph reasoning across Company, Product, and Executive nodes",
    )
    node(draw, (250, 420), 92, BLUE, "Target Co.", "Company")
    node(draw, (620, 300), 82, GREEN, "Battery", "Product")
    node(draw, (1010, 300), 92, BLUE, "Supplier Co.", "Company")
    node(draw, (620, 600), 82, PURPLE, "CEO Zhang", "Executive")
    node(draw, (1010, 600), 92, AMBER, "Partner Co.", "Company")

    arrow(draw, (342, 395), (535, 322), GREEN, 7)
    arrow(draw, (705, 300), (918, 300), GREEN, 7)
    label(draw, (455, 248), "Phi_1: Company -> Product -> Company", GREEN)
    label(draw, (742, 246), "attention 0.72", GREEN)

    arrow(draw, (335, 462), (548, 570), PURPLE, 5)
    arrow(draw, (704, 600), (918, 600), PURPLE, 5)
    label(draw, (455, 676), "Phi_2: Company -> Executive -> Company", PURPLE)
    label(draw, (742, 636), "attention 0.43", PURPLE)

    rounded_box(
        draw,
        (92, 720, 1308, 835),
        "#ffffff",
        "#cbd5e1",
        "Decision signal",
        "Supply-chain terms such as price increase, shortage, delayed delivery, and capacity pressure raise Phi_1 weight.",
        INK,
    )
    save(image, "han_metapath_visualization.png")


def draw_workflow() -> None:
    image, draw = canvas(
        "Multi-Agent Industrial Risk Workflow",
        "From public enterprise text to heterogeneous graph reasoning and strict JSON action output",
    )
    boxes = [
        ((70, 260, 300, 420), BLUE, "Data Sources", "Reports\nAnnouncements\nNews"),
        ((360, 260, 610, 420), GREEN, "Extractor Agent", "Company\nProduct\nExecutive"),
        ((670, 260, 920, 420), CYAN, "Graph Store", "Nodes\nRelations\nMeta-paths"),
        ((980, 260, 1230, 420), PURPLE, "HAN Reasoner", "Attention\n3-hop cascade\nRisk score"),
        ((520, 590, 880, 750), RED, "Action Agent", "Strict JSON\nWarning level\nSuggested action"),
    ]
    for xy, fill, title, body in boxes:
        rounded_box(draw, xy, fill, fill, title, body)

    arrow(draw, (300, 340), (360, 340), INK, 5)
    arrow(draw, (610, 340), (670, 340), INK, 5)
    arrow(draw, (920, 340), (980, 340), INK, 5)
    arrow(draw, (1105, 420), (820, 590), RED, 5)
    arrow(draw, (670, 590), (485, 420), CYAN, 4)

    label(draw, (312, 300), "entity extraction")
    label(draw, (626, 300), "graph build")
    label(draw, (930, 300), "meta-path scoring")
    label(draw, (908, 520), "risk synthesis", RED)
    label(draw, (440, 502), "feedback context", CYAN)
    save(image, "agent_workflow.png")


def draw_cascade() -> None:
    image, draw = canvas(
        "3-hop Risk Cascade Example",
        "Deep cascade analysis for industrial chain warning and enterprise delivery risk",
    )
    steps = [
        ((70, 330, 330, 500), AMBER, "A: Raw Material", "Lithium carbonate\nprice increase"),
        ((400, 330, 660, 500), GREEN, "B: OEM Factory", "Margin pressure\ncapacity squeeze"),
        ((730, 330, 990, 500), CYAN, "C: Core Part", "Shortage risk\nlonger lead time"),
        ((1060, 330, 1320, 500), RED, "D: Target Co.", "Delivery default\ncredit warning"),
    ]
    for xy, fill, title, body in steps:
        rounded_box(draw, xy, fill, fill, title, body)

    arrow(draw, (330, 415), (400, 415), RED, 6)
    arrow(draw, (660, 415), (730, 415), RED, 6)
    arrow(draw, (990, 415), (1060, 415), RED, 6)
    label(draw, (333, 365), "cost pass-through", RED)
    label(draw, (658, 365), "production delay", RED)
    label(draw, (986, 365), "delivery breach", RED)

    rounded_box(
        draw,
        (180, 650, 1220, 780),
        "#ffffff",
        "#cbd5e1",
        "Risk response",
        "Freeze high-risk exposure, verify upstream contracts, monitor inventory, and request alternative supplier evidence.",
        INK,
    )
    save(image, "risk_cascade_example.png")


def main() -> None:
    draw_metapath()
    draw_workflow()
    draw_cascade()
    print(f"Generated assets in {ASSET_DIR}")


if __name__ == "__main__":
    main()

