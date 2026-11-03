#!/usr/bin/env python3
"""
crm_push.py: the CRM step. Dedupes the researched list against the existing customer file and against itself,
then writes a clean import file with the stage set. Any CRM with an API (Close, HubSpot, Salesforce, Zoho)
takes this file, or the pilot wires the same lookup, update or create logic straight into the API.

Usage: python3 crm_push.py --in output/buyers-researched.csv --customers data/customers.csv --out output/crm-import.csv
"""
import argparse, csv, re

def norm_phone(p): return re.sub(r"\D", "", p or "")[-10:]
def norm_name(n): return re.sub(r"[^a-z0-9]", "", (n or "").lower())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--customers", default="data/customers.csv")
    ap.add_argument("--out", default="output/crm-import.csv")
    a = ap.parse_args()
    cust_names, cust_phones = set(), set()
    try:
        for r in csv.DictReader(open(a.customers)):
            cust_names.add(norm_name(r.get("name"))); cust_phones.add(norm_phone(r.get("phone")))
    except FileNotFoundError:
        pass
    cust_phones.discard("")
    rows = list(csv.DictReader(open(a.inp)))
    seen, out, dropped_customer, dropped_dupe = set(), [], 0, 0
    for r in rows:
        k = (norm_name(r["company"]), norm_phone(r.get("phone")))
        if norm_name(r["company"]) in cust_names or (norm_phone(r.get("phone")) and norm_phone(r.get("phone")) in cust_phones):
            dropped_customer += 1; continue
        if k in seen:
            dropped_dupe += 1; continue
        seen.add(k)
        out.append({
            "lead_name": r["company"], "type": r.get("type", ""), "address": r.get("address", ""),
            "phone": r.get("phone", ""), "website": r.get("website", ""),
            "contact_name": r.get("contact_name", ""), "contact_title": r.get("contact_title", ""),
            "contact_email": r.get("contact_email", ""),
            "propane_use": r.get("verification_status", "assumed"), "evidence_url": r.get("evidence_url", ""),
            "score": r.get("score", ""), "stage": "new, not contacted", "source": r.get("source", ""),
            "found_on": r.get("found_on", ""),
        })
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["lead_name"])
        w.writeheader(); w.writerows(out)
    print(f"{len(out)} leads ready for the CRM -> {a.out}")
    print(f"  dropped as existing customers: {dropped_customer}")
    print(f"  dropped as duplicates: {dropped_dupe}")
    print("  stages: new, contacted, replied, quote sent, customer, lost")

if __name__ == "__main__":
    main()
