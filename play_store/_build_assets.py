"""Generates Play Store listing assets from the existing brand logo.

Outputs (all PNG, written next to this script):
  icon_512.png            — high-res app icon for the Play Store listing
  feature_graphic.png     — 1024x500 promo banner (logo + tagline + bg)

The phone screenshots are pulled separately via adb screencap.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
ROOT = HERE.parent
LOGO = ROOT / 'frontend' / 'assets' / 'icons' / 'scancourse-logo.png'

PRIMARY = (30, 64, 175)          # #1E40AF — same as the app
PRIMARY_DARK = (30, 58, 138)     # #1E3A8A
WHITE = (255, 255, 255)
TEXT_HINT = (203, 213, 225)


def find_font(size: int):
    """Best-effort font lookup. Falls back to default if nothing matches."""
    candidates = [
        '/System/Library/Fonts/Supplemental/Arial Black.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/Library/Fonts/Arial Bold.ttf',
        '/System/Library/Fonts/Avenir.ttc',
        '/System/Library/Fonts/Avenir Next.ttc',
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ── 1. App icon 512x512 ────────────────────────────────────────────
print('Building app icon 512x512…')
logo = Image.open(LOGO).convert('RGBA')
icon = Image.new('RGBA', (512, 512), WHITE + (255,))

# If the logo is roughly square we paste it centred at ~90% of the canvas.
# This gives a small white margin around the brand mark.
target = int(512 * 0.9)
logo_resized = logo.resize((target, target), Image.LANCZOS)
offset = ((512 - target) // 2, (512 - target) // 2)
icon.paste(logo_resized, offset, logo_resized)
icon.save(HERE / 'icon_512.png', 'PNG', optimize=True)
print('  → icon_512.png')


# ── 2. Feature graphic 1024x500 ────────────────────────────────────
# Looks like the landing-page hero: blue gradient bg with the logo
# on the left and tagline + app name on the right.
print('Building feature graphic 1024x500…')
W, H = 1024, 500
fg = Image.new('RGB', (W, H), PRIMARY)

# Vertical-ish gradient by blending from PRIMARY_DARK (top-left) to PRIMARY (bottom-right)
grad_overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
gradient_pixels = grad_overlay.load()
for y in range(H):
    for x in range(W):
        t = ((x / W) + (y / H)) / 2
        r = int(PRIMARY_DARK[0] * (1 - t) + PRIMARY[0] * t)
        g = int(PRIMARY_DARK[1] * (1 - t) + PRIMARY[1] * t)
        b = int(PRIMARY_DARK[2] * (1 - t) + PRIMARY[2] * t)
        gradient_pixels[x, y] = (r, g, b, 255)
fg = grad_overlay.convert('RGB')

# Soft "spotlight" highlight in the upper-left
spot = Image.new('RGBA', (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(spot)
sd.ellipse((-150, -200, 500, 400), fill=(255, 255, 255, 28))
spot = spot.filter(ImageFilter.GaussianBlur(radius=80))
fg = Image.alpha_composite(fg.convert('RGBA'), spot).convert('RGB')

# Logo on the left in a white rounded square ("app-store style" pill)
LOGO_BOX = 280
pad = 70
card = Image.new('RGBA', (LOGO_BOX, LOGO_BOX), (0, 0, 0, 0))
cd = ImageDraw.Draw(card)
cd.rounded_rectangle((0, 0, LOGO_BOX, LOGO_BOX), radius=56, fill=WHITE + (255,))
inner = logo.resize((LOGO_BOX - 24, LOGO_BOX - 24), Image.LANCZOS)
card.paste(inner, (12, 12), inner)

# Drop shadow under the logo card
shadow = Image.new('RGBA', (LOGO_BOX + 60, LOGO_BOX + 60), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle(
    (30, 30, LOGO_BOX + 30, LOGO_BOX + 30),
    radius=56, fill=(0, 0, 0, 70))
shadow = shadow.filter(ImageFilter.GaussianBlur(radius=22))
fg_rgba = fg.convert('RGBA')
fg_rgba.paste(shadow, (pad - 30, (H - LOGO_BOX) // 2 - 20), shadow)
fg_rgba.paste(card, (pad, (H - LOGO_BOX) // 2), card)

# Right column: app name + tagline
draw = ImageDraw.Draw(fg_rgba)
x_text = pad + LOGO_BOX + 56
font_big = find_font(70)
font_mid = find_font(34)
font_small = find_font(22)

# "Scancourse"
draw.text((x_text, 158), 'Scancourse', font=font_big, fill=WHITE)

# Tagline
draw.text((x_text, 250), 'Scan your results.',
          font=font_mid, fill=WHITE)
draw.text((x_text, 295), 'Plan your future.',
          font=font_mid, fill=WHITE)

# Footnote
draw.text((x_text, 360), 'For Grade 11 & 12 learners · South Africa',
          font=font_small, fill=TEXT_HINT)

fg_rgba.convert('RGB').save(HERE / 'feature_graphic.png', 'PNG', optimize=True)
print('  → feature_graphic.png')

print('\nDone. Files:')
for p in sorted(HERE.glob('*.png')):
    print(f'  {p.name}  ({p.stat().st_size // 1024} KB)')
