# Vision extract (from Unit 5 Word document)

**Group:** 6  
**Author:** Damian J. Moore  
**Date:** 2026-08-23

## Project vision

Replace a bookstore's paper logbooks and manual ledger with a simple, reliable desktop software program to track inventory, process sales, and order stock.

Three modules:

1. **Inventory tracking** — Replaces paper stock cards. Stores title, author, ISBN/UUID, price, quantity, and shelf location. Updates quantities when books are sold or received.
2. **POS & checkout** — Replaces manual cash-register logs. Calculates totals, tax, and change; updates stock at checkout; logs daily cash/card sales.
3. **Supplier & customer orders** — Replaces physical order notebooks. Tracks incoming supplier orders and customer special requests.

## Roles (source text)

- Product Owner: bookstore owner; backlog; approval.
- Scrum Master: standups, sprint meetings, blockers.
- Development team: two developers, one tester.

This repository maps those hats onto Damian (PO + architecture), Richard (SM + inventory/POS), and Stephen (QA + orders).

## Collaboration

Scrum, two-week sprints, daily standup, review/demo, retrospective. Tools named in the document: Jira, GitHub, Slack. This example uses GitHub issues in place of Jira and pull-request comments in place of Slack.

## Definition of Done (source)

All three modules coded and on one database; paper records entered; system testing with no crashing bugs and accurate tax/stock; owner/staff UAT and PO sign-off; manuals written; code on the production branch; software installed on the store computer.

## Product design (source)

Desktop application, three modules, one central database. Passwords stored as `password_hash`. Transaction and customer-request records restricted and included in backups.
