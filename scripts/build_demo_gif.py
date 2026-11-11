"""Build a lightweight visual walkthrough from the committed dashboard screenshots."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "assets" / "screenshots"
frames = [
    (source / "executive-scorecard.png", "Executive scorecard"),
    (source / "cohort-retention.png", "Retention and account portfolio"),
    (source / "customer-health-drilldown.png", "Customer health and drill-down"),
]
images = []
for path, label in frames:
    image = Image.open(path).convert("RGB")
    image.thumbnail((1280, 720))
    canvas = Image.new("RGB", (image.width, image.height + 52), "#111827")
    canvas.paste(image, (0, 52))
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 18), f"PulseMetrics · {label}", fill="white")
    images.append(canvas)
out = ROOT / "reports" / "pulsemetrics-dashboard-walkthrough.gif"
images[0].save(out, save_all=True, append_images=images[1:], duration=1800, loop=0, optimize=True)
print(f"Wrote {out}")
