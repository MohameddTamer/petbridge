# PetBridge Flutter client

The customer app for PetBridge, in Flutter: one Dart codebase for
Android, iOS, Windows and web. It talks to the existing Python
backend over HTTP and changes nothing on the server side.

## Run it

Point the app at a running backend (default `http://127.0.0.1:8765`,
the backend's own default port) and start it in a browser:

```bash
cd ../backend && python3 app.py
cd ../flutter_app && flutter run -d web
```

To point at another server, pass a define:

```bash
flutter run -d web --dart-define=PETBRIDGE_BASE_URL=http://192.168.1.10:8765
```

Sign in with a demo customer account, for example
`sara@petbridge.local` / `Sara123!`, or browse services and lost pets
as a guest. Booking, pets and breed ID need a signed-in customer.

## What it covers

Home with pets, due items, quick actions and a first-run tour;
the full 35-service directory in 8 categories with prices; service
detail and booking with the price, the 12% commission and the
provider net shown before and after the server confirms; pet pages
with a dashed-stitch health timeline; lost-and-found browsing; and
breed ID through the backend beta endpoint, labelled beta with no
accuracy claims.

## Money

Commission math mirrors the backend exactly: commission is the total
times the rate rounded to two decimals, and the provider net is the
total minus that commission. The booking confirmation shows the
figures the server recorded, never a second calculation.

## What it does not cover yet

Provider portal, admin console, client-provider chat, push or email
notifications, real payments (the backend payment is a simulation),
and store binaries: there is no Android SDK or Xcode on this
machine, so no APK or IPA is built here. The web build is the
verified target on this machine.

## Design

Hand-Drawn Companion: warm paper `#FFFDF8`, ink `#22301F`, crayon
teal `#2E7D6B`, ochre `#E3A72F`. Hand-drawn tape strips, dashed
stitch lines and 2px-stroke icons, painted in code. Handwriting
style is reserved for margin notes and never touches numbers or
prices. English only.
