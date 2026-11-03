# Propane Buyers

Commercial propane prospecting in Claude Code. One command finds the businesses in a service area that run on propane, proves which ones with a URL, drops existing customers, ranks them, and prepares the CRM import and the first message.

## Setup (five minutes)
1. Install Claude Code and Python 3.
2. Copy `.env.example` to `.env` and paste the keys. Serper (Google search and Maps) is the only one needed to find and verify. The other four are for finding decision makers and checking emails and phones, optional.
3. Put existing customers in `data/customers.csv` (name, phone, email) so they are never contacted.
4. Open this folder in Claude Code.

## Run
```
/find-buyers "El Paso, TX"
/find-buyers "El Paso, TX" verify 50
/find-buyers "Las Cruces, NM" verify 20 contacts 5
```
Defaults: verify 10, contacts 0. Everything lands in `output/`.

## What comes out
- `output/buyers.csv` every business found, with its type, phone, website, the propane use that type has, and the source query.
- `output/buyers-researched.csv` the same rows with `verification_status` set to confirmed (evidence_url and snippet filled) or assumed, plus a 1 to 5 score.
- `output/crm-import.csv` deduped, customers removed, stage set, ready for any CRM.
- The first messages print in the chat. Nothing is sent from here.

## Costs
Serper: 1 credit a Maps page (about 10 businesses) and 1 credit a verified row. An area of 240 businesses with 50 verified is about 80 credits.
