import math
from typing import Dict, List, Any

# Simple colour palette
COLOURS = [
    "#3498db",  # blue
    "#e74c3c",  # red
    "#2ecc71",  # green
    "#9b59b6",  # purple
    "#f1c40f",  # yellow
    "#1abc9c",  # teal
    "#e67e22",  # orange
]


def _author_palette(authors: List[str]) -> Dict[str, str]:
    palette = {}
    for i, a in enumerate(authors):
        palette[a] = COLOURS[i % len(COLOURS)]
    return palette


def generate_sentiment_timeline_svg(timeline: List[Dict[str, Any]], width: int = 800, height: int = 300) -> str:
    """Line chart for sentiment_score over time for each author."""
    if not timeline:
        return _placeholder_svg("Timeline", width, height)

    authors = sorted({a for entry in timeline for a in entry["authors"].keys()})
    palette = _author_palette(authors)

    padding = 40
    chart_w = width - padding * 2
    chart_h = height - padding * 2

    # x step per bin
    x_step = chart_w / max(1, (len(timeline) - 1))

    # Build polyline for each author
    polylines = []
    for author in authors:
        points = []
        for idx, entry in enumerate(timeline):
            val = entry["authors"].get(author, {}).get("sentiment_score", 0.5)  # default neutral
            # sentiment_score expected range [-1,1] or 0-1; clamp to 0-1
            if val < 0:
                val = (val + 1) / 2  # convert -1..1 to 0..1
            val = max(0, min(1, val))
            x = padding + idx * x_step
            y = padding + chart_h * (1 - val)
            points.append(f"{x:.2f},{y:.2f}")
        polyline = f'<polyline fill="none" stroke="{palette[author]}" stroke-width="2" points="{" ".join(points)}" />'
        polylines.append(polyline)

    # Legend
    legend_items = []
    legend_y = padding / 2
    legend_x = padding
    for i, author in enumerate(authors):
        legend_items.append(
            f'<rect x="{legend_x}" y="{legend_y}" width="12" height="12" fill="{palette[author]}" />'
        )
        legend_items.append(
            f'<text x="{legend_x + 16}" y="{legend_y + 11}" font-size="12" font-family="Arial">{author}</text>'
        )
        legend_x += 100

    svg = f"""
    <svg id="chart-1" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="#333" />
        <line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#333" />
        {"".join(polylines)}
        {"".join(legend_items)}
    </svg>
    """
    return svg


def generate_radar_chart_svg(metrics_summary: Dict[str, Dict[str, float]], width: int = 400, height: int = 400) -> str:
    """Simple radar chart comparing key metrics per author."""
    if not metrics_summary:
        return _placeholder_svg("Radar", width, height)

    metrics = [
        "toxicity",
        "manipulation",
        "assertiveness",
        "empathy",
        "sentiment_score",
        "emotion_intensity",
    ]
    num_axes = len(metrics)
    cx, cy = width / 2, height / 2
    radius = min(width, height) / 2 - 40
    angle_step = 2 * math.pi / num_axes

    authors = sorted(metrics_summary.keys())
    palette = _author_palette(authors)

    # Axis lines & labels
    axes = []
    for i, metric in enumerate(metrics):
        angle = i * angle_step - math.pi / 2  # start at top
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        axes.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#ccc" />')
        lx = cx + (radius + 15) * math.cos(angle)
        ly = cy + (radius + 15) * math.sin(angle)
        axes.append(f'<text x="{lx}" y="{ly}" font-size="12" font-family="Arial" text-anchor="middle">{metric}</text>')

    # Polygons for each author
    polys = []
    for author in authors:
        points = []
        for i, metric in enumerate(metrics):
            val = metrics_summary[author].get(metric, 0)
            val = max(0, min(1, val))
            r = val * radius
            angle = i * angle_step - math.pi / 2
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x:.2f},{y:.2f}")
        polys.append(f'<polygon points="{" ".join(points)}" fill="{palette[author]}33" stroke="{palette[author]}" stroke-width="1" />')

    svg = f"""
    <svg id="chart-2" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        {"".join(axes)}
        {"".join(polys)}
    </svg>
    """
    return svg


def generate_bar_chart_svg(data: Dict[str, float], title: str, width: int = 600, height: int = 300, chart_id: str = "chart-3") -> str:
    """Generic vertical bar chart."""
    if not data:
        return _placeholder_svg(title, width, height, chart_id)

    items = list(data.items())
    max_val = max(v for _, v in items) or 1
    bar_w = (width - 80) / len(items)
    bars = []
    labels = []
    for i, (label, val) in enumerate(items):
        x = 50 + i * bar_w
        h = (val / max_val) * (height - 60)
        y = height - 40 - h
        colour = COLOURS[i % len(COLOURS)]
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_w * 0.6}" height="{h}" fill="{colour}" />')
        labels.append(f'<text x="{x + bar_w * 0.3}" y="{height - 20}" font-size="12" text-anchor="middle">{label}</text>')

    svg = f"""
    <svg id="{chart_id}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        {"".join(bars)}
        {"".join(labels)}
        <text x="{width/2}" y="20" font-size="16" text-anchor="middle" font-family="Arial">{title}</text>
    </svg>
    """
    return svg


def _placeholder_svg(title: str, width: int, height: int, chart_id: str = "chart-x") -> str:
    return f"""
    <svg id="{chart_id}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#f5f5f5" />
        <text x="{width/2}" y="{height/2}" font-size="16" fill="#777" text-anchor="middle" font-family="Arial">{title}</text>
    </svg>
    """ 