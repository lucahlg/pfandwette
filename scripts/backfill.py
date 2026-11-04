#!/usr/bin/env python3
"""Einmalig: rekonstruiert den Verlauf seit dem Kauf aus dem Basiswert (Yahoo, 1-Min-Kerzen).
Modell: Briefkurs = a * (Kurs - Strike), a wird am Kaufkurs kalibriert (passt auch zu den Live-Kursen);
Geldkurs = Briefkurs - SPREAD.
Die Punkte sind mit "syn": true markiert (kuenstlich)."""
import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

STRIKE, BUY_PRICE, SPREAD = 122.80, 2.68, 0.04
BUY_T = datetime(2026, 11, 3, 14, 51, 23, tzinfo=timezone.utc).timestamp()
F = Path(__file__).resolve().parent.parent / "data" / "history.json"

d = json.loads(F.read_text())
real = [p for p in d["history"] if not p.get("syn")]
first = real[0]
t_end = datetime.fromisoformat(first["t"].replace("Z", "+00:00")).timestamp()

req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/NBIS?interval=1m&range=5d&includePrePost=true",
                             headers={"User-Agent": "Mozilla/5.0"})
r = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
bars = [(t, c) for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c]

def S(t):  # letzter bekannter Basiswert-Kurs vor t
    return [c for bt, c in bars if bt <= t][-1]

a = BUY_PRICE / (S(BUY_T + 30) - STRIKE)
def bid(c): return max(0.01, round(a * (c - STRIKE) - SPREAD, 2))
iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
out = [{"t": iso(BUY_T), "bid": bid(S(BUY_T + 30)), "syn": True}]
last = BUY_T
for bt, c in bars:
    if BUY_T < bt < t_end and bt - last >= 300:
        out.append({"t": iso(bt), "bid": bid(c), "syn": True}); last = bt
d["history"] = out + real
F.write_text(json.dumps(d, separators=(",", ":")))
print("a =", round(a, 4), len(out), "synthetische Punkte;", min(p["bid"] for p in out), "-", max(p["bid"] for p in out))
