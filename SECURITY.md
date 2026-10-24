# Security

## What is implemented

- Passwords are stored as PBKDF2-HMAC-SHA256 hashes with 210,000 iterations and a random 16-byte salt per account. No password is ever stored in plain text.
- Sessions are random 32-byte tokens in a sessions table, sent as Bearer tokens.
- Every database query uses bound parameters; no query is built from user text. An injection test on sign-in proves the rejection.
- Role isolation on the server for every route: a client cannot open provider or admin routes, a provider cannot open admin routes, and narrower admin roles cannot approve or suspend accounts.
- A suspended account has its current session rejected and its next sign-in attempts refused.
- An approval gate on visibility: an unapproved provider's data, services and products never reach the public directory and shop routes.
- Money is computed on the server only. The client never sends a total or a commission; the price comes from the approved service and the commission rate from the system settings at booking time.
- The audit log is protected by database triggers that refuse any update or delete of its rows.
- Interface output is built with DOM elements and textContent for user data in most places, so post and profile text cannot turn into executed HTML.

## Known limits before any public launch

- There is no HTTPS inside the app itself. Deployment sits behind a reverse proxy with transport encryption; cookies are not currently used.
- There is no rate limiting on sign-in yet. It must be added before a public launch, with progressive lockout.
- There is no two-factor authentication yet, although the full report spec mentions it.
- Session tokens currently have no automatic expiry. Expiry and renewal are added before launch.
- File uploads are metadata only in this version, so there is no uploaded-file scanning yet — because there is no binary storage at all.
- Payment gateway keys and accounts do not exist in the code or the repository; when connected at launch they will be environment variables only.

## Reporting

If you notice a vulnerability in a local copy, record it with a clear reproduction description, and never publish real account data in the report.
