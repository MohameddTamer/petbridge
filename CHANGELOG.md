# Changelog

## 0.2.0 — 2026-10-24 — English conversion and the three-identity redesign

- The whole product is English only now: all three portals, the auth pages, API messages, the service taxonomy, the breed profiles, seed data, README, SECURITY and the tests. Layout is LTR everywhere. The Egyptian setting stays, written in English words (Tanta, Cairo, Alexandria; Nile Veterinary Clinic; El Bahr Street).
- One brand, three designed identities (see DESIGN.md): the client portal is a Hand-Drawn Companion (Nunito with Caveat margin notes, washi-taped pet pages, a stitch-line health timeline, a paw-print trail, a hand-circled booking confirmation); the provider portal is a disciplined Bento Studio Console (Sora with IBM Plex Mono money, one large, two medium, four small tiles with live data and decisions inside the tiles); the admin console is a Monochrome Swiss Console (Inter Tight, ruled registers, a permanent audit rail, colour only on approve and reject decisions).
- The brand mark was redrawn in the hand-drawn stroke family, the PWA manifest is English LTR, and the service worker cache moved to v2.
- Backend logic and money math are unchanged: the seed still produces a completed booking of 500 with 60 commission and 440 net, a shop order of 170 with 17 commission, an admin commission total of 77, and the vaccine booking flow still computes 350 with 42 commission and 308 net. The full suite still passes 22 of 22.

## 0.1.0 — 2026-10-24

First working version of the platform.

- Three separate portals over one API and one database: client, provider, admin.
- Accounts with roles, PBKDF2-hashed passwords and Bearer sessions.
- Provider registration with documents and a pending status, and a real approval gate: neither the business nor its services appear in the directory before the admin approves the business, then the service.
- An approved service taxonomy of 35 services in 8 categories.
- Pet profiles with a computed age and health records with due and overdue status.
- A directory with city and category filters, search, reviews, and capacity-based availability slots.
- Bookings with pending, accepted, proposed, rejected, cancelled and completed states, with alternative-time proposals and client replies.
- Platform commission computed on the server and pinned on the booking, at a default 12% adjustable from admin, and a 10% shop commission.
- An admin console with indicators, approval queues, community moderation, account suspension, and an audit log protected from editing and deletion at the database level.
- Lost and found, adoption, community, articles, and a shop with clearly labelled simulated orders.
- A breed identification tool as a local beta flow labelled Beta, behind a single endpoint ready for a real vision model.
- A PWA with a manifest, a service worker and a drawn icon, and a responsive interface.
- Fictional seed data: 8 approved providers in 3 cities, one pending provider, 3 clients, and an admin team in three roles.
- 22 passing API and static-interface tests.
