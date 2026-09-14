"""Render a self-contained GitHub activity illustration from GitHub API data."""

import base64
import datetime as dt
import html
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
USER = "ArchineDai"


def api(*args):
    result = subprocess.run(["gh", "api", *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    start = now.date() - dt.timedelta(days=90)
    query = """query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){createdAt repositories(privacy:PUBLIC,ownerAffiliations:OWNER){totalCount}
      contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions weeks{
      contributionDays{date contributionCount}}}}}}
    """
    result = api("graphql", "-f", f"query={query}", "-f", f"login={USER}",
                 "-f", f"from={start.isoformat()}T00:00:00Z",
                 "-f", f"to={now.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    if result.get("errors"):
        raise RuntimeError("GitHub returned GraphQL errors; existing artwork retained")
    user = result["data"]["user"]
    calendar = user["contributionsCollection"]["contributionCalendar"]
    count = calendar["totalContributions"]
    repos = user["repositories"]["totalCount"]
    joined = user["createdAt"][:4]
    portrait = base64.b64encode((ROOT / "assets/reze.png").read_bytes()).decode("ascii")
    outputs = {}
    for name, colors in {
        "dark": {"bg": "#0d1117", "text": "#e6edf3", "muted": "#9199a6", "accent": "#b6a4d5", "chip": "#161b22", "border": "#30363d", "halo": "#24202f", "heat": ["#1b212a", "#343043", "#635875", "#9480b1", "#c3abdd"]},
        "light": {"bg": "#ffffff", "text": "#24292f", "muted": "#68717c", "accent": "#73618c", "chip": "#f6f8fa", "border": "#d1d9e0", "halo": "#f1edf6", "heat": ["#ebedf0", "#e5dfed", "#c8b9da", "#9a85b2", "#6d5887"]},
    }.items():
        def label(x, y, value, size=14, fill=None, weight=400):
            return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill or colors["text"]}">{html.escape(str(value))}</text>'

        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="850" height="470" viewBox="0 0 850 470" role="img" aria-labelledby="title desc">',
                 '<title id="title">GitHub activity · Reze</title>',
                 f'<desc id="desc">{repos} public repositories; {count} contributions from {start} to {now.date()}. Flutter, React Native, Android. Reze illustration.</desc>',
                 f'<rect width="850" height="470" fill="{colors["bg"]}"/>',
                 f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">',
                 label(24, 57, "Activity", 17, colors["accent"]),
                 label(24, 105, repos, 27, weight=500),
                 label(70, 103, "public repos", 14, colors["muted"]),
                 label(252, 105, count, 27, weight=500),
                 label(322, 103, "contributions", 14, colors["muted"]),
                 label(24, 144, f"On GitHub since {joined}.", 13, colors["muted"]),
                 label(24, 187, f"{start.isoformat()} — {now.date().isoformat()}", 12, colors["muted"])]
        for col, week in enumerate(calendar["weeks"]):
            for day in week["contributionDays"]:
                row = dt.date.fromisoformat(day["date"]).isoweekday() % 7
                n = day["contributionCount"]
                level = 4 if n > 15 else 3 if n > 5 else 2 if n > 1 else 1 if n else 0
                parts.append(f'<rect x="{24 + col * 26}" y="{207 + row * 26}" width="22" height="22" rx="3" fill="{colors["heat"][level]}"><title>{day["date"]}: {n} contributions</title></rect>')
        for x, width, value in [(24, 78, "Flutter"), (110, 122, "React Native"), (240, 83, "Android")]:
            parts.append(f'<rect x="{x}" y="408" width="{width}" height="27" rx="4" fill="{colors["chip"]}" stroke="{colors["border"]}"/>')
            parts.append(label(x + 11, 426, value, 12, colors["accent"]))
        parts.extend([f'<ellipse cx="680" cy="282" rx="94" ry="161" fill="{colors["halo"]}" opacity="0.55"/>',
                      f'<image x="590" y="14" width="170" height="442" href="data:image/png;base64,{portrait}" preserveAspectRatio="xMidYMid meet"/>',
                      '</g></svg>'])
        outputs[name] = "\n".join(parts) + "\n"

    # Fetch and render everything before replacing either published image.
    for name, svg in outputs.items():
        (ROOT / f"assets/profile-{name}.svg").write_text(svg, encoding="utf-8")
    print(f"Updated {now.date()}: {repos} public repositories, {count} contributions")


if __name__ == "__main__":
    main()
