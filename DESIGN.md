# PetBridge — Design Notes

## One brand, three identities

PetBridge is one product with three very different rooms. A pet owner, a clinic owner and a platform moderator do not think alike, do not scan alike, and do not forgive the same things. So the brand is held together by shared DNA — the deep teal `#0E4F45`, the ochre `#D98E1F` family, the drawn paw-and-bridge mark, and tabular numerals everywhere money or dates appear — while each portal gets its own posture, typography and surface logic. A user who lands in the wrong portal should feel it instantly, the way you feel a wrong room in a house.

---

## 1. Client portal — the Hand-Drawn Companion

The client is a person with a cat on their lap, not an operator. The portal behaves like a well-kept follow-up notebook: warm, personal, drawn by hand, but with its numbers kept professionally straight.

**Palette**

| Role | Hex |
| --- | --- |
| Warm white paper | `#FFFDF8` |
| Ink | `#22301F` |
| Crayon teal | `#2E7D6B` |
| Deep teal (shared DNA) | `#0E4F45` |
| Crayon ochre | `#E3A72F` |
| Crayon brick (overdue only) | `#B3402A` |

**Type.** Nunito (400/700/800/900) carries everything: interface, prose and data — a rounded humanist sans that stays legible at small sizes. Caveat (600/700) is used **only** for margin annotations: the note under the hero, the aside in the due panel, the line inside the booking confirmation. Handwriting never touches data, a price, a date or a status. All numerals are tabular.

**Signature moves**

- **Pet profiles are washi-taped notebook pages.** Each pet is a sheet with a translucent tape strip on top, rotated a fraction of a degree — odd pages tilt left, even pages right, the tape alternating teal and ochre. Nothing is a "card grid"; it is a pile of pages.
- **The health timeline runs down a dashed stitch line.** Records are stitches on a seam; the marker dot fills ochre when a record is due soon and brick when it is overdue, so the timeline itself carries the warning before any text is read.
- **One drawn SVG stroke family** does every icon: paw, syringe-adjacent shapes, house, bone, calendar, camera, pin, heart, bag, book — 2px round-capped strokes with slightly imperfect geometry and flat imperfect fills. No icon font, no stock set, no emoji.
- **A dotted paw-print trail** wanders between the hero and the quick actions: a dashed path with paw prints resting on it, the way a pet crosses a clean floor.
- **The booking confirmation is hand-circled.** The single celebration moment in the product: when a booking is sent, an SVG ellipse draws itself around the words "Booking sent", with a Caveat margin note underneath. It is the only animated flourish, and it respects `prefers-reduced-motion`.
- **Radii are hand-cut** (the uneven `255px 18px 225px 18px / 18px 225px 18px 255px` wobble) on hero, buttons and modals — drawn, not machined.

**Deliberate avoidances.** No stat cards, no pill-everything, no purple anything, no glass, no emoji icons, no handwriting on numbers, no animation besides the circle.

---

## 2. Provider portal — the Bento Studio Console

The provider is at work. The studio is disciplined, quiet and dense: a porcelain bench where the day's decisions sit in tiles of deliberately unequal weight.

**Palette**

| Role | Hex |
| --- | --- |
| Warm porcelain | `#F6F4EF` |
| Tile white | `#FFFFFF` |
| Tone steps | `#EFECE5`, `#E7E2D6` |
| Deep teal (shared DNA) | `#0E4F45` |
| Ochre | `#D98E1F` |

Surfaces are separated by **tone steps, never shadows**. The porcelain, the tile white and the two deeper tones do all the layering.

**Type.** Sora for interface and headings; **IBM Plex Mono** for every pound, time, booking figure and table number — money in a studio is machine-read, and it is set like it.

**The bento hierarchy is strict: 1 large, 2 medium, 4 small.**

- **Large tile (2×2) — the booking inbox.** The pending count at display size, and the *next* request written out as a line — service, client, time, total — with its Accept action inside the tile. The tile is deep teal: it is the room's one loud object, because it is the one thing the provider came to do.
- **Medium tile — earnings.** Gross, platform commission and net in Plex Mono, over a row of spark bars: one bar per completed booking's net, oldest to newest, the latest in ochre. The bars are drawn from the real bookings list, never decorative.
- **Medium tile — decisions.** Up to three waiting requests, each with its own Accept and Reject inside the tile. Work is finished where it is seen.
- **Four small tiles** — client rating; shop orders; profile completeness as an honest `n / 4` checklist (approval, services, open slots, documents) that names what is still missing; and quick actions with the services count.

**Deliberate avoidances.** No equal tiles (the classic bento failure), no shadows, no gradients, no stat-card strip above the grid pretending to be a summary, no colour beyond the teal/ochre DNA and brick on Reject.

---

## 3. Admin console — the Monochrome Swiss Console

Administration is a register, not a dashboard. The console is charcoal and hairlines, set tight, and it spends its entire colour budget on two things only: the decisions.

**Palette**

| Role | Hex |
| --- | --- |
| Charcoal | `#131517` |
| Panel | `#1B1E21` |
| Hairline | `#2C3034` |
| Text | `#E8EAEB` |
| Dim | `#9BA1A6` |
| Approval teal (decisions only) | `#2E7D6B` |
| Refusal red (decisions only) | `#C8402F` |

**Type.** Inter Tight, dense and unadorned, for the interface; **IBM Plex Mono** for IDs, timestamps, money columns and the whole audit rail.

**Signature moves**

- **Everything is one continuous ruled register system.** Indicators are ruled cells in a strip — never cards. Queues, users, posts and bookings are full-width ruled tables under heavy top rules; a row *is* the record.
- **The audit log is a permanent right rail**, always on screen, not a page you visit. When a moderator approves or rejects from a queue, the decision lands in the rail in real time — cause and record share one view.
- **Decisions are inline in the row.** Approve is a solid teal block, Reject a red outline that fills on hover; the two-keystroke rhythm of working a queue is select row, decide, watch the rail. Statuses are monochrome text chips: no traffic-light palette anywhere, so the eye is never pulled away from the two coloured verbs.
- The brand mark is rendered greyscale in the console. Even the logo obeys the register.

**Deliberate avoidances.** No colour for status, decoration or emphasis; no cards; no rounded corners (radius is 0 throughout — the console is ruled, not softened); no charts. Precision and alignment carry the design, because in an audit tool, decoration is a liability.

---

## Shared rules

- Tabular numerals in every portal, no exceptions — money and dates never jitter.
- Every native control is drawn: selects get drawn chevrons, file inputs get drawn buttons, date and time inputs are styled to the portal's hand.
- Each portal ships its own Google Fonts pairing with system fallbacks (Segoe UI / Tahoma), so a font outage degrades the voice, not the layout.
- `prefers-reduced-motion` is respected wherever anything moves.
