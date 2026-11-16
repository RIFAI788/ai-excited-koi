"""Render 'Koi Leap' — a giant koi leaping over a neon city at dusk.

Flat-colour vector-style art drawn with PIL at 2x supersampling, then
downscaled to 1024x1024 for smooth edges. No text anywhere.
"""
import math
import random

from PIL import Image, ImageDraw

S = 2            # supersampling factor
W, H = 1024 * S, 1024 * S
random.seed(7)

# ---------- helpers ----------

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bezier(p0, p1, p2, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return x, y


def bezier_tangent(p0, p1, p2, t):
    dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
    dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def rotated_ellipse(cx, cy, rx, ry, angle_deg):
    a = math.radians(angle_deg)
    pts = []
    for i in range(28):
        th = 2 * math.pi * i / 28
        x = rx * math.cos(th)
        y = ry * math.sin(th)
        pts.append((cx + x * math.cos(a) - y * math.sin(a),
                    cy + x * math.sin(a) + y * math.cos(a)))
    return pts


# ---------- canvas ----------

img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)

# dusk sky gradient: deep indigo -> violet -> hot orange horizon
stops = [(0.00, (16, 10, 48)), (0.35, (58, 24, 92)), (0.60, (122, 38, 96)),
         (0.78, (214, 74, 62)), (0.92, (255, 138, 76)), (1.00, (255, 178, 102))]
for y in range(H):
    t = y / H
    for i in range(len(stops) - 1):
        if stops[i][0] <= t <= stops[i + 1][0]:
            f = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
            d.line([(0, y), (W, y)], fill=lerp(stops[i][1], stops[i + 1][1], f))
            break

# stars in the upper sky
for _ in range(110):
    x = random.randint(0, W)
    y = random.randint(0, int(H * 0.42))
    r = random.choice([1, 1, 2, 2, 3]) * S // 2 + 1
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 244, 214))

# ---------- glowing moon (upper right) ----------
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
mx, my, mr = 1560, 430, 250
for r, alpha in [(560, 18), (460, 26), (360, 40), (300, 60)]:
    gd.ellipse([mx - r, my - r, mx + r, my + r], fill=(255, 214, 130, alpha))
img = Image.alpha_composite(img.convert("RGBA"), glow)
d = ImageDraw.Draw(img)
d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(255, 233, 168))
d.ellipse([mx - mr + 46, my - mr + 40, mx - mr + 130, my - mr + 124],
          fill=(244, 208, 128))
d.ellipse([mx + 40, my + 60, mx + 110, my + 130], fill=(244, 208, 128))
d.ellipse([mx - 90, my + 90, mx - 30, my + 150], fill=(244, 208, 128))

# distant skyline silhouette (hazy purple, behind the koi)
for bx, bw, bh in [(0, 260, 260), (230, 180, 380), (390, 240, 300),
                   (620, 160, 430), (770, 220, 330), (980, 200, 400),
                   (1160, 180, 300), (1330, 220, 420), (1540, 200, 310),
                   (1730, 180, 380), (1900, 160, 300)]:
    d.rectangle([bx, H - 330 - bh, bx + bw, H - 280], fill=(64, 32, 88))

# ---------- the koi: a big arc from lower-left water to upper-right moon ----------
P0 = (520, 1380)      # tail, just above the skyline
P1 = (600, 380)       # control — high arc
P2 = (1700, 600)      # head, reaching for the moon
N = 60
pts, widths = [], []
for i in range(N + 1):
    t = i / N
    x, y = bezier(P0, P1, P2, t)
    # body width: thin tail, fat belly, slightly narrower head
    w = (22 + 105 * math.sin(math.pi * min(1.0, t * 1.12)) ** 0.9) * S
    if t > 0.85:
        w *= 1.0 - (t - 0.85) * 0.8
    pts.append((x, y))
    widths.append(max(w, 14))

# body outline polygon (offset along normals)
left, right = [], []
for i, (x, y) in enumerate(pts):
    tx, ty = bezier_tangent(P0, P1, P2, i / N)
    nx, ny = -ty, tx
    left.append((x + nx * widths[i], y + ny * widths[i]))
    right.append((x - nx * widths[i], y - ny * widths[i]))
d.polygon(left + right[::-1], fill=(255, 250, 240))

# orange dorsal band (upper half of the body)
band = []
for i, (x, y) in enumerate(pts):
    tx, ty = bezier_tangent(P0, P1, P2, i / N)
    nx, ny = -ty, tx
    band.append((x - nx * widths[i] * 0.02, y - ny * widths[i] * 0.02))
    band.append((x - nx * widths[i] * 1.0, y - ny * widths[i] * 1.0))
upper = [band[i] for i in range(0, len(band), 2)]
lower = [band[i] for i in range(1, len(band), 2)]
d.polygon(upper + lower[::-1], fill=(255, 122, 26))

# orange patches on the belly side
for t, rx, ry in [(0.30, 85, 50), (0.52, 110, 62), (0.70, 95, 55)]:
    x, y = bezier(P0, P1, P2, t)
    tx, ty = bezier_tangent(P0, P1, P2, t)
    ang = math.degrees(math.atan2(ty, tx))
    d.polygon(rotated_ellipse(x + ty * widths[int(t * N)] * 0.30,
                              y - tx * widths[int(t * N)] * 0.30,
                              rx, ry, ang), fill=(255, 122, 26))

# black spots
for t, rx, ry in [(0.42, 42, 26), (0.62, 34, 22), (0.80, 30, 18)]:
    x, y = bezier(P0, P1, P2, t)
    tx, ty = bezier_tangent(P0, P1, P2, t)
    ang = math.degrees(math.atan2(ty, tx))
    d.polygon(rotated_ellipse(x, y, rx, ry, ang), fill=(26, 18, 40))

# tail fin: a forked fan swept out to the left of the tail tip
tx0, ty0 = pts[0]
d.polygon([(tx0, ty0), (140, 1180), (60, 1330), (180, 1420)],
          fill=(255, 122, 26))
d.polygon([(tx0, ty0), (150, 1500), (80, 1640), (200, 1560)],
          fill=(255, 250, 240))

# dorsal fin: one smooth fin along the top of the arc
fin_outer, fin_inner = [], []
for i in range(21):
    t = 0.42 + 0.20 * i / 20
    x, y = bezier(P0, P1, P2, t)
    tx, ty = bezier_tangent(P0, P1, P2, t)
    nx, ny = -ty, tx
    bump = 110 * math.sin(math.pi * i / 20) ** 1.2
    fin_inner.append((x - nx * widths[int(t * N)] * 0.95,
                      y - ny * widths[int(t * N)] * 0.95))
    fin_outer.append((x - nx * (widths[int(t * N)] + bump),
                      y - ny * (widths[int(t * N)] + bump)))
d.polygon(fin_inner + fin_outer[::-1], fill=(255, 140, 40))

# pectoral fin below the belly
x, y = bezier(P0, P1, P2, 0.58)
tx, ty = bezier_tangent(P0, P1, P2, 0.58)
nx, ny = -ty, tx
d.polygon([(x + nx * widths[35], y + ny * widths[35]),
           (x + nx * (widths[35] + 190) - tx * 140,
            y + ny * (widths[35] + 190) - ty * 140),
           (x + nx * (widths[35] + 80) - tx * 260,
            y + ny * (widths[35] + 80) - ty * 260)],
          fill=(255, 178, 92))

# head: rounded head cap, big eye, mouth, short whiskers
hx, hy = pts[-1]
tx, ty = bezier_tangent(P0, P1, P2, 1.0)
nx, ny = -ty, tx
ang = math.degrees(math.atan2(ty, tx))
d.polygon(rotated_ellipse(hx - tx * 30, hy - ty * 30, 130, 105, ang),
          fill=(255, 250, 240))
d.polygon(rotated_ellipse(hx - tx * 55 - nx * 20, hy - ty * 55 - ny * 20,
                          110, 62, ang), fill=(255, 122, 26))
ex, ey = hx - tx * 75 + nx * 12, hy - ty * 75 + ny * 12
d.ellipse([ex - 34, ey - 34, ex + 34, ey + 34], fill=(26, 18, 40))
d.ellipse([ex - 13, ey - 16, ex + 8, ey + 5], fill=(255, 255, 255))
d.arc([hx - tx * 150 - 70, hy - ty * 150 - 70, hx - tx * 150 + 70,
       hy - ty * 150 + 70], start=210, end=320, fill=(200, 60, 40), width=9)
for sgn in (1, -1):
    d.line([(hx - tx * 110 + nx * sgn * 26, hy - ty * 110 + ny * sgn * 26),
            (hx - tx * 220 + nx * sgn * 120, hy - ty * 220 + ny * sgn * 120)],
           fill=(255, 250, 240), width=8)

# ---------- water splash arcing under the koi ----------
splash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(splash)
for i in range(40):
    t = i / 39
    x = 320 + t * 1150 + random.randint(-26, 26)
    y = 1500 - 520 * math.sin(math.pi * t) ** 0.8 + random.randint(-34, 34)
    r = random.randint(8, 30)
    sd.ellipse([x - r, y - r, x + r, y + r], fill=(190, 240, 255, 235))
    if i % 3 == 0:
        sd.ellipse([x - r // 2, y - r // 2, x + r // 2, y + r // 2],
                   fill=(255, 255, 255, 255))
img = Image.alpha_composite(img.convert("RGBA"), splash)
d = ImageDraw.Draw(img)

# ---------- water at the bottom ----------
d.rectangle([0, 1780, W, H], fill=(8, 42, 62))
for i in range(26):
    y = 1810 + i * 9
    d.line([(0, y), (W, y)], fill=(14 + i, 62 + i, 88 + i))
# splash crown where the tail leaves the water
cx0, cy0 = 260, 1780
for dx, hgt, wdt in [(-220, 220, 80), (-130, 320, 100), (-30, 260, 90),
                     (70, 360, 110), (170, 260, 90), (260, 190, 80)]:
    d.polygon([(cx0 + dx - wdt // 2, cy0), (cx0 + dx, cy0 - hgt),
               (cx0 + dx + wdt // 2, cy0)], fill=(190, 240, 255))
d.ellipse([cx0 - 330, cy0 - 60, cx0 + 330, cy0 + 40], fill=(220, 246, 255))

# ---------- foreground neon city ----------
random.seed(11)
bx = 0
while bx < W:
    bw = random.randint(120, 260)
    bh = random.randint(180, 620)
    top = H - bh
    d.rectangle([bx, top, bx + bw, H], fill=(10, 8, 28))
    # rooftop antenna on some towers
    if random.random() < 0.4:
        d.line([(bx + bw // 2, top), (bx + bw // 2, top - 90)],
               fill=(255, 80, 120), width=6)
        d.ellipse([bx + bw // 2 - 10, top - 110, bx + bw // 2 + 10, top - 90],
                  fill=(255, 80, 120))
    # lit windows
    for wy in range(top + 30, H - 20, 44):
        for wx in range(bx + 18, bx + bw - 18, 40):
            if random.random() < 0.42:
                col = random.choice([(255, 214, 130), (120, 230, 255),
                                     (255, 120, 170), (255, 240, 200)])
                d.rectangle([wx, wy, wx + 20, wy + 26], fill=col)
    # neon roof edge
    d.rectangle([bx, top, bx + bw, top + 10],
                fill=random.choice([(255, 80, 120), (60, 220, 255),
                                    (255, 180, 60), (170, 90, 255)]))
    bx += bw + random.randint(6, 26)

# neon reflections on the water
for _ in range(60):
    x = random.randint(0, W - 120)
    y = random.randint(1850, H - 20)
    ln = random.randint(40, 160)
    col = random.choice([(255, 80, 120), (60, 220, 255), (255, 180, 60)])
    d.line([(x, y), (x + ln, y)], fill=col, width=5)

img = img.convert("RGB").resize((1024, 1024), Image.LANCZOS)
img.save("/home/hatch/workspace/makefun-bounty/ai-excited-01/repo/entry.png",
         optimize=True)
print("saved", img.size)
