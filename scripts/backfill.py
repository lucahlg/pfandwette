#!/usr/bin/env python3
"""Einmalig: rekonstruiert den Verlauf seit dem Kauf aus dem Basiswert (Yahoo, 5-Min-Kerzen).
Modell: Turbo-Preis = a * (Kurs - Strike). a wird zwischen Kaufkurs und erstem echten BNP-Kurs linear angepasst.
Die Punkte sind mit "syn": true markiert (kuenstlich)."""
import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

STRIKE, BUY_PRICE = 122.80, 2.68
BUY_T = datetime(2026, 11, 3, 14, 51, 23, tzinfo=timezone.utc).timestamp()
F = Path(__file__).resolve().parent.parent / "data" / "history.json"

d = json.loads(F.read_text())
real = [p for p in d["history"] if not p.get("syn")]
first = real[0]
t_end = datetime.fromisoformat(first["t"].replace("Z", "+00:00")).timestamp()

req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/NBIS?interval=5m&range=5d&includePrePost=true",
                             headers={"User-Agent": "Mozilla/5.0"})
r = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
bars = [(t, c) for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c]

def S(t):  # letzter bekannter Basiswert-Kurs vor t
    return [c for bt, c in bars if bt <= t][-1]

a0 = BUY_PRICE / (S(BUY_T) - STRIKE)
a1 = first["bid"] / (S(t_end) - STRIKE)
out = [{"t": datetime.fromtimestamp(BUY_T, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "bid": BUY_PRICE, "syn": True}]
for bt, c in bars:
    if BUY_T < bt < t_end:
        a = a0 + (a1 - a0) * (bt - BUY_T) / (t_end - BUY_T)
        out.append({"t": datetime.fromtimestamp(bt, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "bid": max(0.01, round(a * (c - STRIKE), 2)), "syn": True})
d["history"] = out + real
F.write_text(json.dumps(d, separators=(",", ":")))
print(len(out), "synthetische Punkte;", min(p["bid"] for p in out), "-", max(p["bid"] for p in out))
