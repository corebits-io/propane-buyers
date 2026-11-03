# Propane Buyers: commercial propane prospecting in Claude Code

Built for Texas Gas and Liquids Downstream Services, El Paso. Finds the businesses that buy propane inside a service area, proves which ones actually use it, drops existing customers, ranks them, finds the decision maker and writes the first message. One command: `/find-buyers "El Paso, TX"`.

## Who buys propane and how we know
- Warehouses, distribution centers, 3PLs, cold storage: indoor forklifts run on propane cylinders. Evidence: forklift operator job posts, forklifts in Google photos, a cylinder cage by the dock.
- Manufacturers and plants: forklifts, ovens, furnaces, boilers.
- Hotels: kitchens, pools, laundry, patio heat.
- Restaurants and food trucks: kitchens, patio heaters, grills.
- Car washes and laundromats: water heating and dryers.
- Construction and farms: temporary heat, roasters, dryers.
- Anything off the natural gas main heats with propane.
"Confirmed" means one of those is on the record with a URL. No URL, it stays "assumed" and ranks lower. Never upgrade a row without a source.

## The pipeline (scripts in `scripts/`, outputs in `output/`)
1. `find_buyers.py` Google Maps via Serper, every business by category in the area. Source query and date on every row. `--exclude data/customers.csv` marks existing customers. 1 Serper credit a page, about 10 rows a page.
2. `research_buyers.py` one web search per business for the propane signals. Sets confirmed with `evidence_url` and `evidence_snippet`, or leaves assumed. 1 credit a row.
3. Claude scores 1 to 5 and prints the ranked table (rules in the skill).
4. `find_people.py --domain <site> --titles operations,facilities,plant,warehouse,general manager,owner --enrich 1` the decision maker with a verified email (Prospeo, Better Contact fallback, BounceBan check). `verify_phone.py` checks a mobile (ClearoutPhone).
5. `fetch_site.py <site>` the website text, so the first message is about them.
6. Claude writes the first message per business from the evidence and the site text. Printed in the chat, nothing is sent from here. The sales team approves copy and audiences before anything goes into the email tool.
7. `crm_push.py` dedupes against customers and itself and writes `output/crm-import.csv` with the stage set. The pilot wires the same lookup, update or create logic into the CRM API (Close, HubSpot, Salesforce, Zoho) and tracks new, contacted, replied, quote sent, customer, lost.

## Keys
`.env` in this folder: SERPER_API_KEY, PROSPEO_API_KEY, BETTERCONTACT_API_KEY, BOUNCER_API_KEY (BounceBan), CLEAROUTPHONE_API_KEY. Never printed, never committed.

## Rules
- Nothing sends from this folder. Outreach runs in the client's email tool after approval.
- Every row keeps its source and its verification status. No invented evidence, no invented people.
- Existing customers never get a message: `data/customers.csv` (name, phone, email) is the exclusion list.
- Unsubscribes and replies are handled in the email tool; replies go to the sales team, not to the automation.
