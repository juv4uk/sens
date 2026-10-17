"""Dependency-free SVG plots derived directly from recorded samples."""

from report import summarize


def boxplot_svg(series: dict[str, list[int]], title: str) -> str:
    width, height = 760, 100 + 70 * len(series)
    maximum = max(max(values) for values in series.values())
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="white"/>',
            f'<text x="20" y="28" font-family="sans-serif" font-size="18">{title} — latency (ns)</text>']
    for fraction, label in ((0, "0"), (0.5, f"{maximum/2:.0f}"), (1, f"{maximum}")):
        x = 180 + 540 * fraction
        rows += [f'<line x1="{x}" y1="45" x2="{x}" y2="{height-15}" stroke="#ddd"/>',
                 f'<text x="{x}" y="{height-3}" text-anchor="middle" font-family="sans-serif" font-size="11">{label}</text>']
    for index, (label, values) in enumerate(series.items()):
        stats = summarize({"samples": [{"elapsed_ns": value} for value in values], "n": len(values),
                           "implementation": "", "rss_kib": {}})
        y = 60 + index * 70
        scale = lambda x: 180 + 540 * x / maximum
        ordered = sorted(values)
        q1, q3 = ordered[len(ordered)//4], ordered[(3*len(ordered))//4]
        rows += [f'<text x="12" y="{y+5}" font-family="sans-serif" font-size="13">{label}</text>',
                 f'<line x1="{scale(min(values))}" y1="{y}" x2="{scale(max(values))}" y2="{y}" stroke="#333"/>',
                 f'<rect x="{scale(q1)}" y="{y-12}" width="{max(1, scale(q3)-scale(q1))}" height="24" fill="#7aa6d8" stroke="#234"/>',
                 f'<line x1="{scale(stats["median_ns"])}" y1="{y-12}" x2="{scale(stats["median_ns"])}" y2="{y+12}" stroke="#900" stroke-width="2"/>']
    return "\n".join(rows + ["</svg>", ""])


def histogram_svg(series: dict[str, list[int]], title: str, bins: int = 20) -> str:
    width, height = 760, 420
    maximum = max(max(values) for values in series.values())
    colors = ["#3569a8", "#cf7133"]
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="white"/>',
            f'<text x="20" y="28" font-family="sans-serif" font-size="18">{title} — latency histogram (ns)</text>']
    for fraction in (0, 0.5, 1):
        x = 50 + 680 * fraction
        rows += [f'<line x1="{x}" y1="65" x2="{x}" y2="370" stroke="#ddd"/>',
                 f'<text x="{x}" y="395" text-anchor="middle" font-family="sans-serif" font-size="11">{maximum*fraction:.0f}</text>']
    counts_all = []
    histograms = []
    for values in series.values():
        counts = [0] * bins
        for value in values:
            counts[min(bins - 1, value * bins // (maximum + 1))] += 1
        histograms.append(counts)
        counts_all.extend(counts)
    y_max = max(counts_all) or 1
    for series_index, (label, _) in enumerate(series.items()):
        rows.append(f'<text x="{30+series_index*180}" y="55" fill="{colors[series_index%len(colors)]}" font-family="sans-serif">{label}</text>')
        for bin_index, count in enumerate(histograms[series_index]):
            x = 50 + bin_index * 34
            bar_h = 320 * count / y_max
            rows.append(f'<rect x="{x+series_index*8}" y="{370-bar_h}" width="12" height="{bar_h}" fill="{colors[series_index%len(colors)]}" opacity="0.65"/>')
    return "\n".join(rows + ["</svg>", ""])
