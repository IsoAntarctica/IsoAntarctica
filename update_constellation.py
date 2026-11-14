"""Update the star strip from the public GitHub contribution calendar."""
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        if tag != "td":
            return
        cell = dict(attrs)
        if "data-date" in cell and cell.get("data-level") in {"0", "1", "2", "3", "4"}:
            self.days[date.fromisoformat(cell["data-date"])] = int(cell["data-level"])


def main():
    request = Request(
        f"https://github.com/users/{sys.argv[1]}/contributions",
        headers={"User-Agent": "profile-constellation"},
    )
    with urlopen(request, timeout=30) as response:
        calendar = Calendar()
        calendar.feed(response.read().decode("utf-8"))
    if len(calendar.days) < 350:
        raise ValueError("Incomplete contribution calendar")

    last_day = max(calendar.days)
    sunday = last_day - timedelta(days=(last_day.weekday() + 1) % 7)
    colors = ("#3c4962", "#7c8cae", "#9eb4d1", "#b9a6d6", "#a8d4c4")
    radii = (0.85, 1.65, 2.4, 3.05, 3.65)
    stars = []
    for day, level in sorted(calendar.days.items()):
        week = (day - sunday).days // 7 + 52
        if week < 0:
            continue
        x = 51 + week * 16.5
        y = 348 + ((day.weekday() + 1) % 7) * 12
        effect = ' class="blink late"' if level == 4 and len(stars) % 3 == 0 else ""
        stars.append(
            f'    <circle cx="{x:g}" cy="{y}" r="{radii[level]}" fill="{colors[level]}"{effect}/>'
        )

    asset = Path("assets/constellation.svg")
    svg = asset.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(<!-- contribution-stars:start -->)\s*.*?(<!-- contribution-stars:end -->)",
        lambda match: match[1] + "\n" + "\n".join(stars) + "\n    " + match[2],
        svg,
        flags=re.DOTALL,
    )
    if count != 1:
        raise ValueError("Expected one contribution star panel")
    if svg != updated:
        asset.write_text(updated, encoding="utf-8", newline="\n")
    print(f"Rendered {len(stars)} days through {last_day}")


if __name__ == "__main__":
    main()