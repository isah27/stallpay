# Devpost submission draft — StallPay

Fill this into the PayPal AI Hackathon Devpost form on Thursday. Do not submit until the video, public repository, and hosted demo URL are in place. The video link below is still a placeholder.

## Title

StallPay

## Tagline (140 characters or fewer)

A shop agent that quotes a real promo, invoices on PayPal only after a clear yes, and checks fake payment proof against PayPal.

Character count: 125.

## Built with

- PayPal sandbox Invoicing API (create, send, get, remind, webhooks)
- Python, FastAPI, Jinja, SQLite
- Optional OpenAI-compatible chat model (Baseten-compatible endpoint; default `meta-models/muse-spark-open-1026`) for draft replies, extraction, receipt field proposals, and briefing copy
- Browser Speech Synthesis for the morning briefing, with a written fallback
- Render (free web service) at https://stallpay.onrender.com/

## Demo URL

https://stallpay.onrender.com/

## Repository

https://github.com/isah27/stallpay

## Video

PLACEHOLDER — public YouTube URL, under 3 minutes, no unlicensed music. Script is in `docs/VIDEO_SCRIPT.md`. Not recorded yet.

## Story / description

Small sellers in every country close deals in Instagram, WhatsApp, and Telegram. A buyer picks an item, hears a price, sometimes tries to bargain, and later sends an edited receipt as proof. There is often no invoice, and no reliable way to see whether the money actually arrived.

StallPay is a shop agent for that job. A judge opens the site with no login and sees a clean shop chat: “Select the shop you want to buy from.” They pick one of three equal shops — a tailor in Lagos, a jeweler in Mexico City, or a textile seller in Jaipur. The agent lists the items and asks what they want. Messages appear in the chat immediately. After the buyer chooses an item, the agent states the real catalog price. If the seller has configured a promo, it quotes the list price and the promo price, with the actual expiry date and time. It never invents a discount or a fake deadline. If the buyer tries to bargain, the agent politely says the promo price is already the best price. A PayPal sandbox invoice and pay link appear only after the buyer clearly says yes to that item and price. If the buyer sends a payment screenshot, StallPay may read the fields, but PayPal’s invoice status is what decides. The image never marks the order paid. Seller tools — the invoice board, reminders, a morning briefing, and paste-a-chat — live on a separate page.

PayPal is central: create, send, get, remind, and payment webhooks (with a Refresh GET as backup). Invoices are issued in USD, with the seller’s currency and a labelled, dated conversion printed in the notes. AI drafts language; it does not move money or set the price.

Published, reproducible results (pytest or `/metrics`): 15/15 adversarial scripts in English, Nigerian Pidgin, Spanish, and Hindi never quoted a price other than the list or active promo; 3/3 expired-promo cases never offered the old deal; false invoice rate 0 on the agreement-gate suite; 4/4 fake payment proofs were not confirmed and 1/1 genuine PayPal-paid proof was confirmed, with 0 false alarms; the original 5 Lagos demo chats still extract and pass, and 3/3 failure cases are still blocked before PayPal.

Limits, stated honestly: sandbox only; no official WhatsApp, Instagram, or Telegram API; not a forensic photoshop detector; no live local-currency settlement.

## How PayPal is used

See the README table. In short: the invoice is created only after the checker passes; send does not email the recipient; GET is the ground truth for the board and for every receipt check; remind sends a seller-tone note on unpaid invoices; webhooks update Paid, with Refresh as backup.

## How AI is used

Optional model drafts multilingual shop replies, structured extraction, receipt field proposals, reminder copy, and the morning briefing. If the key is missing or the model is slow, scripted replies and a heuristic extractor still run the demo. Ordinary code locks the price, the agreement gate, and invoice creation.

## Testing instructions for judges

1. Open https://stallpay.onrender.com/, or run the README local path in mock mode (no keys required). The first visit after idle time on the free host can take about a minute.
2. The first line is “Select the shop you want to buy from.” The shop is in English unless you change the language picker (English, Español, हिन्दी, Pidgin, or Français). Pick Joyería Sofía. Choose the silver hoop earrings (tap or type, including a local name such as “aretes”). Your choice should appear in the chat straight away. Read the list price and the promo, including when it ends. Try to bargain it down; the price should not change. Then say clearly that you want it, for example “Okay I want it.”
3. Only then should the chat hide and an order summary appear, with Proceed with PayPal and I’ve already paid. Under those buttons, the sandbox test buyer login (fake money) is shown on the order summary, with copy buttons for the email and password. Click I’ve already paid before paying — it should say PayPal has not confirmed payment yet. In mock mode, open Proceed with PayPal and click pay, then I’ve already paid again. In live sandbox mode, use that test buyer login to pay, then click I’ve already paid until it confirms.
4. There is no receipt or proof upload. Payment is confirmed only by PayPal’s invoice status.
5. Open Seller tools for the invoice board, Write briefing, and Play.
6. Open `/metrics` for the published tables.

Use sandbox or `@example.com` emails only.

## Submission checklist (still to finish)

- [x] Working prototype
- [x] Public repository: https://github.com/isah27/stallpay
- [x] Hosted no-login demo: https://stallpay.onrender.com/
- [ ] Public YouTube video under 3 minutes
- [ ] Description, tools, and models filled in
- [ ] Submit before Thursday, 12 November 2026, 9:00 PM Lagos, ideally by 7:00 PM
