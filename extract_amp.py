"""
Extracts the gold & path from logo.svg, computes its bounding box
in SVG-space (after the translate/scale transform), and writes amp.svg.
"""

# The transform in logo.svg is: translate(0,841) scale(0.1,-0.1)
# So: x_svg = x_path * 0.1
#     y_svg = 841 - y_path * 0.1

TRANSFORM_TX, TRANSFORM_TY = 0, 841
TRANSFORM_SX, TRANSFORM_SY = 0.1, -0.1

def path_to_svg(x_path, y_path):
    return x_path * TRANSFORM_SX + TRANSFORM_TX, y_path * TRANSFORM_SY + TRANSFORM_TY

# Parse a very simplified bounding box from the path d attribute
# by iterating absolute M/L/C coordinates after expanding relative ones.
def approx_bbox(d):
    """Very rough bbox: collect all absolute x,y after expanding moves."""
    import re
    # Tokenise
    tokens = re.findall(r'[MmCcLlHhVvSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', d)
    xs, ys = [], []
    i = 0
    cx, cy = 0.0, 0.0  # current point (path coordinates)
    cmd = 'M'
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
            continue
        def num():
            nonlocal i
            v = float(tokens[i]); i += 1; return v
        if cmd in ('M', 'L'):
            cx, cy = num(), num()
            xs.append(cx); ys.append(cy)
        elif cmd in ('m', 'l'):
            dx, dy = num(), num()
            cx += dx; cy += dy
            xs.append(cx); ys.append(cy)
        elif cmd == 'C':
            x1,y1 = num(),num(); x2,y2 = num(),num(); cx,cy = num(),num()
            for xv,yv in ((x1,y1),(x2,y2),(cx,cy)): xs.append(xv); ys.append(yv)
        elif cmd == 'c':
            dx1,dy1 = num(),num(); dx2,dy2 = num(),num(); ddx,ddy = num(),num()
            for dx,dy in ((dx1,dy1),(dx2,dy2),(ddx,ddy)):
                xs.append(cx+dx); ys.append(cy+dy)
            cx += ddx; cy += ddy
        elif cmd in ('Z','z'):
            pass
        else:
            # skip unknown
            i += 1
    return min(xs), min(ys), max(xs), max(ys)


# Read logo.svg
with open('logo.svg', 'r', encoding='utf-8') as f:
    svg = f.read()

import re
# Find the gold path
m = re.search(r'<path fill="#b89a55" d="([^"]+)"', svg)
if not m:
    raise RuntimeError("Gold path not found")

path_d = m.group(1)
px_min, py_min, px_max, py_max = approx_bbox(path_d)

print(f"Path bbox (path coords): x={px_min:.1f}..{px_max:.1f}  y={py_min:.1f}..{py_max:.1f}")

# Convert to SVG space
x_min_svg, y_at_pymax = path_to_svg(px_min, py_max)  # pymax → smallest y_svg (top)
x_max_svg, y_at_pymin = path_to_svg(px_max, py_min)  # pymin → largest y_svg (bottom)

# Add a small margin
PAD = 5
vb_x = x_min_svg - PAD
vb_y = y_at_pymax - PAD
vb_w = (x_max_svg - x_min_svg) + PAD * 2
vb_h = (y_at_pymin - y_at_pymax) + PAD * 2

print(f"SVG viewBox: {vb_x:.3f} {vb_y:.3f} {vb_w:.3f} {vb_h:.3f}")

amp_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb_x:.3f} {vb_y:.3f} {vb_w:.3f} {vb_h:.3f}">
  <g transform="translate(0.000000,841.000000) scale(0.100000,-0.100000)" stroke="none">
    <path fill="#b89a55" d="{path_d}"/>
  </g>
</svg>
'''

with open('amp.svg', 'w', encoding='utf-8') as f:
    f.write(amp_svg)

print("Written amp.svg")
