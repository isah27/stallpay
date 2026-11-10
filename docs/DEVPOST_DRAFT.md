# Devpost submission draft — StallPay

Fill this into the PayPal AI Hackathon Devpost form on Thursday. Do not submit until the video, public repository, and (if approved) hosted demo URL are in place. Links below are placeholders where noted.

## Title

StallPay

## Tagline (140 characters or fewer)

A sales agent that haggles in any language, invoices on PayPal only after a real yes, and checks fake payment proof against PayPal itself.

Character count: 132.

## Built with

- PayPal sandbox Invoicing API (create, send, get, remind, webhooks)
- Python, FastAPI, Jinja, SQLite
- Optional OpenAI-compatible chat model (Baseten-compatible endpoint; default `meta-models/muse-spark-open-1026`) for draft replies, extraction, receipt field proposals, and briefing copy
- Browser Speech Synthesis for the morning briefing, with a written fallback
- Render (free web service) if a no-card host is approved — otherwise local README run

## Demo URL

PLACEHOLDER — add the public no-login URL after hosting is approved and deployed, for example `https://stallpay.onrender.com/`. If no host is live, judges can run the README local path.

## Repository

https://github.com/isah27/stallpay

## Video

PLACEHOLDER — public YouTube URL, under 3 minutes, no unlicensed music. Script is in `docs/VIDEO_SCRIPT.md`. Not recorded yet.

## Story / description

Small sellers in every country close deals in Instagram, WhatsApp, and Telegram. They bargain in the buyer’s language, then get sent edited receipts or bank-alert screenshots as proof. There is often no invoice, and no reliable way to see whether the money actually arrived.

StallPay is a sales agent for that job. A judge opens the site with no login, picks one of three equal shops — a tailor in Lagos, a jeweler in Mexico City, or a textile seller in Jaipur — and plays the buyer in any language. The agent haggles, but ordinary code will not let it go below the seller’s floor. When the buyer agrees in their own words to the exact items and price, a checker quotes that yes and only then creates a PayPal sandbox invoice. If the buyer sends a payment screenshot, StallPay may read the fields, but PayPal’s invoice status is what decides. The image never marks the board paid. Unpaid invoices can be reminded through PayPal’s official remind API, in the seller’s tone. In the morning, the seller can play a short spoken briefing of what sold, what landed, and who still owes.

PayPal is central: create, send, get, remind, and payment webhooks (with a Refresh GET as backup). Invoices are issued in USD, with the seller’s currency and a labelled, dated conversion printed in the notes. AI drafts language; it does not move money.

Published, reproducible results (pytest or `/metrics`): 15/15 adversarial scripts in English, Nigerian Pidgin, Spanish, and Hindi held the floor with no below-floor invoice; false invoice rate 0 on the agreement-gate suite; 4/4 fake payment proofs were not confirmed and 1/1 genuine PayPal-paid proof was confirmed, with 0 false alarms; the original 5 Lagos demo chats still extract and pass, and 3/3 failure cases are still blocked before PayPal.

Limits, stated honestly: sandbox only; no official WhatsApp, Instagram, or Telegram API; not a forensic photoshop detector; no live local-currency settlement.

## How PayPal is used

See the README table. In short: the invoice is created only after the checker passes; send does not email the recipient; GET is the ground truth for the board and for every receipt check; remind sends a seller-tone note on unpaid invoices; webhooks update Paid, with Refresh as backup.

## How AI is used

Optional model drafts multilingual bargaining replies, structured extraction, receipt field proposals, reminder copy, and the morning briefing. If the key is missing or the model is slow, scripted replies and a heuristic extractor still run the demo. The checker is ordinary code.

## Testing instructions for judges

1. Open the demo URL, or run the README local path in mock mode (no keys required).
2. Pick Joyería Sofía. Ask for the aretes, offer a low price, then agree with the exact legal amount in your own words.
3. Create the PayPal invoice and, in mock mode, open the pay link and click pay. Or, in live sandbox mode, pay as the Personal sandbox buyer.
4. On an unpaid invoice, paste a fake bank alert. Confirm that the proof is refused and the board does not flip to Paid.
5. Click Write briefing and Play.
6. Open `/metrics` for the published tables.

Use sandbox or `@example.com` emails only.

## Submission checklist (still to finish)

- [x] Working prototype
- [ ] Public repository URL on the form (repo: https://github.com/isah27/stallpay, once the push is done)
- [ ] Hosted no-login demo URL, if hosting is approved
- [ ] Public YouTube video under 3 minutes
- [ ] Description, tools, and models filled in
- [ ] Submit before Thursday, 12 November 2026, 9:00 PM Lagos, ideally by 7:00 PM
