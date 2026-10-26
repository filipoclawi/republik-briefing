# Republik Briefing

Weekly, lightly filtered German previews based on the actual Republik newsletter emails.

Public URL: <https://filipoclawi.github.io/republik-briefing/>

- Saturday–Friday editions with permanent archive paths and navigation throughout
- One concise original preview per newsletter title; no full email or article republication
- Clean direct links extracted from the matching email; no invented destinations
- Reading times only when supplied by the source; otherwise `Lesezeit nicht angegeben`
- No recipient data, email addresses, mailbox identifiers, tracking parameters or private attribution

## Ongoing editions and preservation

The root always mirrors the newest archive. `editions.json` records each edition's date range and card count. Newly reconciled editions also record `sourceCount` and `status`; a `partial` edition has an explicit timezone-aware `asOf` cutoff and a visible Zwischenstand notice.

When extending or finalizing a partial edition, **merge rather than replace** its existing cards with later newsletters. Preserve older cards, stable card anchors, original clean URLs and previous editions. Deduplicate by normalized newsletter title and clean URL; source-ID reconciliation belongs exclusively in private action records. Reconcile all exact-label Inbox newsletters, including already-read and historical mail, rather than restricting discovery to the current day. Keep partial-week source messages until the complete Friday edition is merged and verified.

Email bodies are the sole editorial source. Publisher access failures do not invalidate substantive email-grounded previews; do not imply a full article was read. Service notices are not editorial filler. Before generating or publishing, verify live authorization to required source and publishing services; stop if authentication fails.

## Verification

Run `python3 tests/ui_smoke.py` for the local desktop/mobile archive, filter, link, duration, privacy and overflow checks. The test uses an ephemeral local HTTP server.

Run `BASE_URL=https://filipoclawi.github.io/republik-briefing/ python3 tests/ui_smoke.py` against the deployed site. Publication also requires a clean diff/privacy audit, the exact commit reported built by Pages, and live byte equality for root, manifest, assets and affected archives. A successful push alone is not a verified publication.
