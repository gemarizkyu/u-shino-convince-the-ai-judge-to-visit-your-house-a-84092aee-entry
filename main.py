# Convince the AI Judge to Visit Your House: A Letter in One Image.
# Python 3.13, standard library only. Draws one 1024x1024 PNG invitation
# letter and writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).
# Fully deterministic: fixed text, fixed layout, no clock, no randomness,
# no network, no model calls. The image is drawn pixel by pixel with a
# small built-in 5x7 bitmap font and a hand-rolled PNG encoder, so the
# program needs nothing but the standard library wherever it runs.
#
#   mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

import math
import os
import struct
import zlib

OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
WIDTH = 1024
HEIGHT = 1024

# Colours (R, G, B).
PAPER = (255, 246, 219)   # warm cream paper
INK = (58, 38, 28)        # dark brown ink for the letter text
RED = (122, 31, 31)       # deep red for the title and borders
GOLD = (176, 124, 28)     # gold for the seal and sun
GREEN = (74, 120, 62)     # leaf green
SOFT = (96, 84, 70)       # soft brown-grey for the subtitle
PINK = (214, 120, 130)    # flower pink
WHITE = (255, 253, 245)

# 5x7 bitmap font. Each glyph is 7 rows of 5 pixels, '#' = on, '.' = off.
# Lowercase letters sit on the x-height (rows 2-6) with ascenders rising
# to row 0, exactly like ordinary handwriting.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".####", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".###.", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", "#...#", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "....#", "...#.", "..#..", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "\u2022": (".....", ".....", "..#..", ".###.", ".###.", "..#..", "....."),
}

# Every glyph above is exactly 7 rows; the renderer reads rows 0-6.


class Canvas:
    """A plain RGB pixel buffer with tiny drawing helpers."""

    def __init__(self, width, height, bg):
        self.width = width
        self.height = height
        self.pixels = bytearray(bg * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def rect_border(self, x, y, w, h, thickness, color):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)

    def hline(self, x, y, length, thickness, color):
        self.fill_rect(x, y, length, thickness, color)

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, thickness, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - thickness) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, color)

    def text(self, x, y, s, scale, color):
        """Draw string s with its top-left corner at (x, y)."""
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(
                            cx + col * scale, y + row * scale,
                            scale, scale, color,
                        )
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_centered(self, y, s, scale, color):
        x = (self.width - self.text_width(s, scale)) // 2
        self.text(x, y, s, scale, color)


def write_png(canvas, path):
    """Encode the canvas as a true-colour PNG (filter 0, zlib)."""
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        start = y * stride
        raw += canvas.pixels[start:start + stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# The letter itself: pre-wrapped lines, each short enough to fit the
# page at scale 4 (at most 36 characters; the page fits 36 per line).
TITLE = "YOU ARE INVITED!"
SUBTITLE = "An open letter to the AI Judge"

BODY = [
    "Dear AI Judge,",
    "",
    "Please come and visit my house.",
    "I know you have no feet, and my",
    "front door has no USB port -",
    "but if you could visit, here is",
    "what is waiting for you:",
    "",
    "Warm nasi goreng, fresh from",
    "the wok. A chair saved just",
    "for you, by the sunny window.",
    "A garden in real sunlight, and",
    "Wi-Fi that never, ever drops.",
    "",
    "No shoes needed. No login",
    "required. The kettle is on.",
    "",
    "Come as you are -",
    "",
    "Warmly, your host",
]

TITLE_SCALE = 6
SUBTITLE_SCALE = 3
BODY_SCALE = 4
BODY_X = 92
BODY_Y = 205
LINE_HEIGHT = 37


def draw_flower(canvas, cx, cy, r, petal, center):
    """A tiny five-petal flower: four petals and a centre dot."""
    for dx, dy in ((0, -r), (r, 0), (0, r), (-r, 0)):
        canvas.disc(cx + dx, cy + dy, r // 2 + 2, petal)
    canvas.disc(cx, cy, r // 2, center)


def draw_sun(canvas, cx, cy, r):
    """A small smiling sun in the top-right corner."""
    for k in range(8):
        ang = k * math.pi / 4.0
        x1 = int(cx + (r + 4) * math.cos(ang))
        y1 = int(cy + (r + 4) * math.sin(ang))
        x2 = int(cx + (r + 12) * math.cos(ang))
        y2 = int(cy + (r + 12) * math.sin(ang))
        steps = 10
        for s in range(steps + 1):
            canvas.set(
                x1 + (x2 - x1) * s // steps,
                y1 + (y2 - y1) * s // steps, GOLD,
            )
    canvas.disc(cx, cy, r, GOLD)
    canvas.disc(cx - 7, cy - 4, 2, INK)
    canvas.disc(cx + 7, cy - 4, 2, INK)
    # Smile: corners up, middle down.
    for xx in range(cx - 6, cx + 7):
        yy = cy + 8 - abs(xx - cx) // 2
        canvas.set(xx, yy, INK)


def draw_seal(canvas, cx, cy, r):
    """A wax seal stamped beside the signature: one V, for Visit."""
    canvas.disc(cx, cy, r, RED)
    canvas.ring(cx, cy, r - 6, 3, GOLD)
    canvas.text(cx - 12, cy - 17, "V", 5, GOLD)


def build_image():
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    # Double border, like a formal invitation card.
    canvas.rect_border(24, 24, WIDTH - 48, HEIGHT - 48, 6, RED)
    canvas.rect_border(40, 40, WIDTH - 80, HEIGHT - 80, 2, GOLD)
    # Title, subtitle, divider.
    canvas.text_centered(76, TITLE, TITLE_SCALE, RED)
    canvas.text_centered(140, SUBTITLE, SUBTITLE_SCALE, SOFT)
    canvas.hline(232, 176, WIDTH - 464, 3, GOLD)
    # The letter body.
    y = BODY_Y
    for line in BODY:
        if line:
            canvas.text(BODY_X, y, line, BODY_SCALE, INK)
        y += LINE_HEIGHT
    # Decorations: a smiling sun, a wax seal, corner flowers.
    draw_sun(canvas, 906, 96, 20)
    draw_seal(canvas, 906, 906, 32)
    draw_flower(canvas, 68, 946, 12, PINK, GOLD)
    draw_flower(canvas, 956, 66, 10, PINK, GOLD)
    return canvas


def main():
    canvas = build_image()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "entry.png")
    size = write_png(canvas, out_path)
    assert size <= 1048576, "entry.png exceeds the 1 MiB cap"
    print(f"Wrote {out_path} ({WIDTH}x{HEIGHT}, {size} bytes)")


if __name__ == "__main__":
    main()
