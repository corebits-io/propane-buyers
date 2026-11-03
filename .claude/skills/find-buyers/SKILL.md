---
name: find-buyers
description: Commercial propane prospecting in one command. Finds every warehouse, plant, 3PL, hotel, restaurant and service business in a service area off Google Maps, checks each for propane evidence (confirmed with a URL, or assumed), drops existing customers, scores and ranks, finds the decision maker, writes the first message, and prepares the CRM import. Run as /find-buyers "<City, ST>" with optional "verify N" and "contacts N".
---

# /find-buyers "<City, ST>" [verify N] [contacts N]

Defaults: verify 10, contacts 0. Work from the project root. Print each step's result in the chat as it lands. Never invent a row, an evidence URL or a person.

## 1. Find
```
python3 scripts/find_buyers.py --area "<City, ST>" --pages 2 --exclude data/customers.csv --out output/buyers.csv
```
Print the count by type.

## 2. Verify (N rows)
```
python3 scripts/research_buyers.py --in output/buyers.csv --out output/buyers-researched.csv --limit N
```
Print how many confirmed and how many stay assumed.

## 3. Qualify and rank
Read `output/buyers-researched.csv`. Add a `score` column (write the file back with it):
- 5 confirmed, heavy use: forklift fleet, plant heat, hotel with pool and kitchen
- 4 confirmed, moderate use: restaurant patio or kitchen, car wash, laundromat
- 3 assumed, type with likely use: warehouse, 3PL, manufacturer
- 2 assumed, light use
- 1 existing customer or no fit
Print the top 15 as a table: company, type, score, verification_status, evidence_terms, decision_maker_title, phone.

## 4. Contacts (N rows, costs credits, only when asked)
For the top N rows with a website:
```
python3 scripts/find_people.py --domain <domain> --titles operations,facilities,plant,warehouse,general manager,owner --enrich 1 --out output/people-<domain>.csv
```
Write contact_name, contact_title, contact_email, contact_linkedin into the row.

## 5. Write
For the top five rows run `python3 scripts/fetch_site.py <website>` when there is a website, then write one first message each, under 80 words: "Hi <First or team>," first line names what you found (the forklift fleet, the patio, the pool), one line on what the supplier does for that kind of business (cylinder exchange on a schedule, bulk tank fills, same day delivery inside the service area), one ask with a named day, "let me know" close. No hyphens. Print them. Nothing sends from here.

## 6. CRM
```
python3 scripts/crm_push.py --in output/buyers-researched.csv --customers data/customers.csv --out output/crm-import.csv
```
Print the counts. Say in one line that the pilot pushes this through the CRM API with a lookup before every create.
