#!/usr/bin/env python3
"""
find_buyers.py: every business of a given kind inside a service area, off Google Maps via Serper,
with the propane signal, the source and a verification status on every row.

Usage:
  python3 find_buyers.py --area "El Paso, TX" --out buyers.csv
  python3 find_buyers.py --area "El Paso, TX" --categories "warehouse,hotel" --pages 3 --out buyers.csv
  python3 find_buyers.py --area "El Paso, TX" --exclude customers.csv --people 10 --out buyers.csv

Needs SERPER_API_KEY in .env in the project root (same file find_people.py reads). Serper: 1 credit a page.
--exclude drops rows whose name or phone matches an existing customer file (columns name, phone).
--people N runs find_people.py --domain on the first N rows with a website and adds the operations contact.
"""
import argparse, csv, json, os, re, subprocess, sys, urllib.request
from datetime import date

ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
FIND_PEOPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "find_people.py")

# category searched on Maps -> (buyer type, why they buy propane, who signs)
CATEGORIES = {
    "warehouse":            ("warehouse",     "forklift fleet, cylinder exchange",     "warehouse manager, operations manager"),
    "distribution center":  ("warehouse",     "forklift fleet, cylinder exchange",     "operations manager, facilities manager"),
    "logistics company":    ("3PL",           "forklift fleet, yard trucks",           "director of operations"),
    "cold storage":         ("warehouse",     "forklift fleet, backup heat",           "plant manager"),
    "manufacturing plant":  ("manufacturer",  "forklifts, process heat, ovens",        "plant manager, maintenance manager"),
    "metal fabrication":    ("manufacturer",  "forklifts, cutting and heat treat",     "plant manager"),
    "food manufacturer":    ("manufacturer",  "forklifts, ovens, boilers",             "plant manager"),
    "hotel":                ("hotel",         "kitchen, pool and laundry heat",        "general manager, chief engineer"),
    "restaurant":           ("restaurant",    "kitchen, patio heaters, grills",        "owner, general manager"),
    "food truck":           ("restaurant",    "cooking cylinders",                     "owner"),
    "car wash":             ("service",       "water heating",                         "owner"),
    "laundromat":           ("service",       "dryers and water heating",              "owner"),
    "construction company": ("construction",  "temporary heat, equipment",             "project manager"),
    "farm":                 ("agriculture",   "crop drying, roasters, irrigation",     "owner"),
}

def load_key():
    for line in open(ENV):
        if line.startswith("SERPER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("SERPER_API_KEY missing in .env")

def serper_places(key, q, page):
    body = json.dumps({"q": q, "gl": "us", "hl": "en", "page": page}).encode()
    req = urllib.request.Request("https://google.serper.dev/places", data=body,
                                 headers={"X-API-KEY": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("places", [])

def norm_phone(p):
    return re.sub(r"\D", "", p or "")[-10:]

def domain_of(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)", url or "")
    return m.group(1).lower() if m else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", required=True, help='service area, e.g. "El Paso, TX"')
    ap.add_argument("--categories", default=",".join(CATEGORIES), help="comma list, see CATEGORIES")
    ap.add_argument("--pages", type=int, default=2, help="Maps pages per category, about 10 rows a page")
    ap.add_argument("--exclude", help="existing customers CSV with name and phone columns")
    ap.add_argument("--people", type=int, default=0, help="find the operations contact on the first N rows with a website")
    ap.add_argument("--out", default="buyers.csv")
    a = ap.parse_args()

    key = load_key()
    existing_names, existing_phones = set(), set()
    if a.exclude:
        for r in csv.DictReader(open(a.exclude)):
            existing_names.add((r.get("name") or "").strip().lower())
            existing_phones.add(norm_phone(r.get("phone")))

    rows, seen = [], set()
    for cat in [c.strip() for c in a.categories.split(",") if c.strip()]:
        btype, why, who = CATEGORIES.get(cat, ("other", "unknown", "owner"))
        for page in range(1, a.pages + 1):
            try:
                places = serper_places(key, f"{cat} in {a.area}", page)
            except Exception as e:
                print(f"serper failed on '{cat}' page {page}: {e}", file=sys.stderr); break
            if not places: break
            for p in places:
                k = p.get("cid") or (p.get("title", "").lower(), p.get("address", ""))
                if k in seen: continue
                seen.add(k)
                name = p.get("title", "")
                phone = p.get("phoneNumber", "")
                status = "existing customer" if (name.lower() in existing_names or (norm_phone(phone) and norm_phone(phone) in existing_phones)) else "assumed"
                rows.append({
                    "company": name, "type": btype, "category_on_maps": p.get("category", cat),
                    "address": p.get("address", ""), "phone": phone, "website": p.get("website", ""),
                    "rating": p.get("rating", ""), "reviews": p.get("ratingCount", ""),
                    "propane_signal": why, "decision_maker_title": who,
                    "verification_status": status, "source": f"Google Maps via Serper, query '{cat} in {a.area}'",
                    "found_on": date.today().isoformat(),
                    "contact_name": "", "contact_title": "", "contact_email": "", "contact_linkedin": "",
                })
    rows = [r for r in rows if r["verification_status"] != "existing customer"] + [r for r in rows if r["verification_status"] == "existing customer"]

    if a.people:
        done = 0
        for r in rows:
            if done >= a.people: break
            d = domain_of(r["website"])
            if not d or r["verification_status"] == "existing customer": continue
            out = f"/tmp/fb_{d.replace('.', '_')}.csv"
            try:
                subprocess.run([sys.executable, FIND_PEOPLE, "--domain", d, "--titles",
                                "operations,facilities,plant,warehouse,general manager,owner,maintenance",
                                "--enrich", "1", "--out", out], capture_output=True, text=True, timeout=180)
                if os.path.exists(out):
                    for pr in csv.DictReader(open(out)):
                        r["contact_name"] = pr.get("name") or pr.get("full_name", "")
                        r["contact_title"] = pr.get("title", "")
                        r["contact_email"] = pr.get("email", "")
                        r["contact_linkedin"] = pr.get("linkedin_url") or pr.get("linkedin", "")
                        break
            except Exception as e:
                print(f"people lookup failed on {d}: {e}", file=sys.stderr)
            done += 1

    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["company"])
        w.writeheader(); w.writerows(rows)
    kinds = {}
    for r in rows: kinds[r["type"]] = kinds.get(r["type"], 0) + 1
    print(f"{len(rows)} businesses in {a.area} -> {a.out}")
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]): print(f"  {k}: {v}")
    print(f"  marked existing customer: {sum(1 for r in rows if r['verification_status']=='existing customer')}")

if __name__ == "__main__":
    main()
