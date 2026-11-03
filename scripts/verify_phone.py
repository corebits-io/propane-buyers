#!/usr/bin/env python3
"""Verify phone numbers with ClearoutPhone. Usage: verify_phone.py +923001234567 [+44...]
Key: CLEAROUTPHONE_API_KEY in .env in the project root (never printed). Prints number, status, line type, carrier, country."""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

def key():
    for line in open(ENV):
        if line.startswith("CLEAROUTPHONE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("CLEAROUTPHONE_API_KEY missing")

def verify(number, k):
    req = urllib.request.Request("https://api.clearoutphone.io/v1/phonenumber/validate",
                                 data=json.dumps({"number": number}).encode(),
                                 headers={"Authorization": f"Bearer:{k}", "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        return {"number": number, "status": f"http {e.code}", "raw": e.read().decode()[:200]}
    r = d.get("data", {}) if isinstance(d, dict) else {}
    return {"number": number, "status": r.get("status"), "line_type": r.get("line_type"),
            "carrier": r.get("carrier"), "country": r.get("country_name") or r.get("country_code"),
            "international": r.get("international_format")}

if __name__ == "__main__":
    k = key()
    for n in sys.argv[1:]:
        print(json.dumps(verify(n, k)))
