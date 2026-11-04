#!/usr/bin/env python3
"""Holt den aktuellen Kurs von der BNP-Paribas-Produktseite und haengt ihn an data/history.json an."""
import json, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ISIN = "DE000PU1SV45"
URL = f"https://derivate.bnpparibas.com/product-details/{ISIN}/"
OUT = Path(__file__).resolve().parent.parent / "data" / "history.json"
MAX_POINTS = 5000

def num(s):
    s = re.sub(r"[^\d,.\-+]", "", s).replace(".", "").replace(",", ".")
    return float(s)

def field(html, name, item=None):
    pat = rf'data-field="{name}" data-item="({re.escape(item) if item else "[^\"]+"})"[^>]*>([^<]*)<'
    m = re.search(pat, html)
    return m.group(2).strip() if m else None

def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf8", "ignore")
    bid, ask = field(html, "bid"), field(html, "ask")
    if not bid or not ask:
        sys.exit("Kurs nicht gefunden")
    ko = re.search(r"Abstand Knock-Out</span></th><td[^>]*>(.*?)</td>", html)
    point = {
        "t": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bid": num(bid),
        "ask": num(ask),
        "koDistance": num(re.sub(r"<[^>]+>", "", ko.group(1))) if ko else None,
        "leverage": num(field(html, "leverage") or "0") or None,
        "quoteTime": field(html, "quotetime"),
    }
    data = {"isin": ISIN, "history": []}
    if OUT.exists():
        data = json.loads(OUT.read_text())
    h = data["history"]
    last = h[-1] if h else None
    if last and all(last.get(k) == point[k] for k in ("bid", "ask", "quoteTime")):
        print("unveraendert"); return
    h.append(point)
    data["history"] = h[-MAX_POINTS:]
    data["updated"] = point["t"]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print("neu:", point)

if __name__ == "__main__":
    main()
