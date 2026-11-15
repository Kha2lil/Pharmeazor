"""Télécharge le robots.txt de chaque source de data/metadata/sources.csv pour lecture."""
import csv
from pathlib import Path
from urllib.parse import urlparse
import requests

ROOT = Path(__file__).resolve().parent.parent
out = ROOT / "data" / "metadata" / "robots"
out.mkdir(parents=True, exist_ok=True)

with open(ROOT / "data" / "metadata" / "sources.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        url = (row.get("url") or "").strip()
        if not url:
            print(f"[--] {row['source']}: pas d'URL")
            continue
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        try:
            r = requests.get(base + "/robots.txt", timeout=20,
                             headers={"User-Agent": "PharmeazorStudentProject"})
            (out / f"{row['source']}.txt").write_text(r.text, encoding="utf-8")
            print(f"[{r.status_code}] {row['source']}: {base}/robots.txt ({len(r.text)} caractères)")
        except Exception as e:
            print(f"[ERR] {row['source']}: {e}")