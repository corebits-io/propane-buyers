#!/usr/bin/env python3
"""
research_buyers.py: the evidence pass. For each business in a find_buyers.py CSV, one Serper web search for
propane use signals (forklift, patio, commercial kitchen, propane, boiler). Records the best URL and snippet
as evidence and sets verification_status to "confirmed" or leaves "assumed". One Serper credit a row.

Usage:
  python3 research_buyers.py --in buyers.csv --out buyers-researched.csv --limit 20
"""
import argparse, csv, json, os, re, sys, urllib.request

ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

SIGNALS = {
    "warehouse":    ["forklift", "forklifts", "propane", "lift truck", "pallet"],
    "3PL":          ["forklift", "forklifts", "propane", "yard truck", "fleet"],
    "manufacturer": ["forklift", "propane", "oven", "furnace", "boiler", "heat treat"],
    "hotel":        ["pool", "kitchen", "restaurant", "laundry", "patio", "propane"],
    "restaurant":   ["patio", "grill", "kitchen", "outdoor seating", "propane", "food truck"],
    "service":      ["propane", "water heater", "dryer", "boiler"],
    "construction": ["propane", "heater", "equipment"],
    "agriculture":  ["propane", "roaster", "dryer", "irrigation"],
    "other":        ["propane", "forklift"],
}

def load_key():
    for line in open(ENV):
        if line.startswith("SERPER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("SERPER_API_KEY missing in .env")

def search(key, q):
    body = json.dumps({"q": q, "gl": "us", "hl": "en", "num": 10}).encode()
    req = urllib.request.Request("https://google.serper.dev/search", data=body,
                                 headers={"X-API-KEY": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("organic", [])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    key = load_key()
    rows = list(csv.DictReader(open(a.inp)))
    for r in rows:
        r.setdefault("evidence_url", ""); r.setdefault("evidence_snippet", ""); r.setdefault("evidence_terms", "")
    done = 0
    for r in rows:
        if done >= a.limit: break
        if r.get("verification_status") == "existing customer": continue
        terms = SIGNALS.get(r.get("type", "other"), SIGNALS["other"])
        parts = [x.strip() for x in r.get("address", "").split(",")]
        city = parts[-2] if len(parts) >= 3 else ""
        q = f'"{r["company"]}" {city} ' + " OR ".join(terms[:4])
        try:
            hits = search(key, q)
        except Exception as e:
            print(f"search failed on {r['company']}: {e}", file=sys.stderr); done += 1; continue
        best = None
        for h in hits:
            text = (h.get("title", "") + " " + h.get("snippet", "")).lower()
            found = [t for t in terms if t in text]
            link = h.get("link", "").lower()
            site = re.sub(r"^https?://(www\.)?", "", r.get("website", "").lower()).split("/")[0]
            own_site = bool(site) and site in link
            local = bool(city) and city.lower() in text
            name = re.sub(r"[^a-z0-9 ]", "", r["company"].lower()).strip()
            junk = any(d in link for d in ("wikimedia", "wikipedia", "esuperhosting", "yellowpages", "mapquest"))
            if found and name in text and (own_site or local) and not junk:
                best = (h, found); break
        if best:
            h, found = best
            r["verification_status"] = "confirmed"
            r["evidence_url"] = h.get("link", "")
            r["evidence_snippet"] = re.sub(r"\s+", " ", h.get("snippet", ""))[:240]
            r["evidence_terms"] = ", ".join(found)
        done += 1
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    c = sum(1 for r in rows if r["verification_status"] == "confirmed")
    print(f"{done} researched, {c} confirmed, {done - c} still assumed -> {a.out}")

if __name__ == "__main__":
    main()
