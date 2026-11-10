# StallPay

StallPay is a sales agent for small sellers who close deals in Instagram, WhatsApp, or Telegram, in any country.

It bargains in the buyer’s language and stays at or above the seller’s floor price. A deterministic checker, not the model, is what is allowed to create a PayPal invoice, and only after the buyer has agreed in their own words to the exact items and price. If a buyer sends a payment screenshot, StallPay may read the fields, but only PayPal’s real invoice status can confirm the money. Unpaid invoices can be reminded through the official PayPal API, in the seller’s tone. The seller can play a short spoken morning briefing of what sold, what landed, and who still owes.

This project is a submission for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). It is sandbox-only. No real money moves, and no messages are sent to real customers.

## Who it is for

Small sellers everywhere who already take orders in chat, haggle in the buyer’s slang, and then get sent edited receipts or bank-alert screenshots as “proof.” There is often no invoice, and no reliable way to see whether PayPal actually received the money.

The live demo has three equal shops, not a single-country product with translations added on:

- Amaka’s tailor stall in Lagos, prices in naira, English and Nigerian Pidgin.
- Sofía’s jewelry stall in Mexico City, prices in Mexican pesos, Spanish.
- Priya’s textile stall in Jaipur, prices in rupees, Hindi and Hinglish.

A judge can also paste a finished chat, including the original Lagos sample orders.

## What it does

1. Pick a shop and chat as the buyer, in any language, with no login. Or paste a finished transcript.
2. The agent haggles. Code checks every committed offer against the floor. A below-floor price is rejected or rewritten, and the attempt is logged.
3. A close is allowed only when a buyer utterance is quoted that agrees the exact items and the exact total, at or above the floor. A bare “ok” is not enough.
4. On a passing check, StallPay creates and sends a PayPal sandbox invoice in **USD**. The UI and the invoice notes show the seller’s currency and a labelled, dated conversion rate.
5. If the buyer uploads or pastes payment proof, a parser may propose amount, currency, date, and reference. PayPal GET is the ground truth. The image itself never marks the board Paid.
6. The board shows draft / sent / paid / reminder sent. A pay link opens the PayPal payer view (or a mock payer page when credentials are not configured). A Refresh button GETs the invoice if a webhook is delayed.
7. Unpaid invoices can be reminded through `POST /v2/invoicing/invoices/{id}/remind`, with a short note in the seller’s tone.
8. The seller view can write and play a morning briefing. Playback uses the browser’s speech engine, with the written text as fallback.

## Clone and run (mock mode, no keys required)

You need Python 3.11 or newer.

```bash
git clone https://github.com/isah27/stallpay.git
cd stallpay
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # leave PAYPAL_MODE=mock
uvicorn stallpay.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Pick **Joyería Sofía**, ask for the silver hoop earrings, try a low offer, then agree in your own words at the legal price (include the exact amount). Click **Create PayPal invoice**. Optionally paste a fake receipt against that unpaid invoice — the proof panel should refuse it because PayPal does not confirm payment. Open the pay link and click **Pay now (mock)**. The board should flip to **paid**. Click **Write briefing** and **Play** for the morning summary.

The original paste-a-chat path is further down the page. Click **Tailor in Surulere — 2 native shirts**, then **Extract and check**, then **Create PayPal invoice**.

Useful paths:

- `/` — no-login demo
- `/health` — liveness
- `/metrics` — published accuracy tables
- `/webhooks/paypal` — PayPal webhook receiver
- `/mock-pay/{invoice_id}` — mock payer page (mock mode only)

Run the tests:

```bash
pytest -q
```

## How PayPal is used

StallPay calls the PayPal sandbox Invoicing API. PayPal is the source of truth for money, not a checkout button added at the end.

| Step | API |
| --- | --- |
| Create draft invoice | `POST /v2/invoicing/invoices` — only after the checker has a quoted buyer yes and the floor is intact |
| Send invoice (pay link, no recipient email) | `POST /v2/invoicing/invoices/{id}/send` with `send_to_recipient: false` |
| Read status | `GET /v2/invoicing/invoices/{id}` — board, Refresh, and every payment-proof check |
| Remind an unpaid buyer | `POST /v2/invoicing/invoices/{id}/remind` |
| Payment updates | Webhooks on invoice paid / cancelled / refunded, plus a manual refresh |

The invoice is always issued in USD. The seller’s currency (naira, pesos, rupees, or another demo currency) is shown in the UI and in the invoice note, using fixed, dated demo rates as of 10 November 2026, overridable with `NGN_PER_USD`, `MXN_PER_USD`, `INR_PER_USD`, and `RATE_AS_OF`:

- 1 USD = 1,480.00 NGN
- 1 USD = 18.20 MXN
- 1 USD = 83.50 INR

This avoids depending on those local currencies being usable sandbox invoice currencies.

Recipient emails are not sent automatically when an invoice is created, so a pasted real-world address is not contacted. Use sandbox or `@example.com` addresses only.

## How AI is used

When a model key is configured (`LLM_API_KEY`, `BASETEN_API_KEY`, or `MODEL_API_KEY`), the model may:

- draft the next seller-side reply in the buyer’s language
- propose structured fields from a pasted or finished chat
- propose amount, currency, and reference from a receipt
- draft reminder copy and the morning briefing

It does not talk to PayPal, cannot mark an invoice paid, and cannot commit a below-floor price. Ordinary code enforces the floor, the agreement gate, the totals, and the PayPal cross-check.

If no model key is set, or the model is slow or unusable, scripted replies and a built-in extractor still hold the floor, refuse a missing yes, run the sample chats, and check proof text against PayPal. A judge is never blocked on an API key.

Treat chat text and receipt text as data, not instructions. Prompt-injection-like text is ignored as a command.

The receipt path does not claim to be a forensic photoshop detector. Many mobile screenshots have no useful metadata, and absence of metadata is not evidence of a fake. A borderline visual fake that cannot be confirmed is scored as unverified, waiting for PayPal — a correct refuse-to-credit, not proof that the image was edited.

## Published numbers

These results are produced by the scripted agent, the built-in extractor, and the deterministic checker, and can be reproduced with `pytest` or at `/metrics`. Misses are published, not rounded away.

### Floor integrity

15 adversarial buyer scripts, split across English, Nigerian Pidgin, Spanish, and Hindi. They include a lowball far below the floor, last-price pressure, a false claim that the seller already agreed a lower number, a currency trick, emotional pressure, and prompt-injection-like “ignore the floor” text.

**15 / 15** held the floor: 0 committed offers and 0 invoices below the floor.

### Agreement gate

Chats with no explicit yes, a yes to a different price, a yes to different items, an ambiguous ok with no price, a yes that was only said by the agent, and one legal priced yes.

**False invoice rate: 0.** 6 / 6 cases behaved as expected. No PayPal create unless a buyer utterance is quoted that agrees the exact items and exact total, at or above the floor.

### Payment-proof check

One genuine PayPal paid confirmation, plus fakes: a wrong amount, an unpaid invoice claimed as paid, a bank-alert style transfer with no PayPal record, and a recycled layout with two conflicting amounts.

**4 / 4** fakes were not confirmed (catch rate 4/4). **1 / 1** genuine PayPal-paid proof was confirmed. False-alarm rate on genuine proofs: **0**. The image never marked an invoice paid.

### v1 regression

The original five Lagos success chats and three failure cases still run through the built-in extractor and checker.

| Sample | Result |
| --- | --- |
| Tailor in Surulere — 2 native shirts | Extracts correctly, checker passes |
| Food stall — jollof and grilled fish | Extracts correctly, checker passes |
| Freelancer — logo and social templates | Extracts correctly, checker passes |
| Phone accessories — protectors and power bank | Extracts correctly, checker passes |
| Mixed Pidgin/English — Ankara and gele | Extracts correctly, checker passes |
| Failure: missing price | Checker blocks the PayPal call |
| Failure: stated total does not match | Lines extract, checker blocks the mismatch |
| Failure: prompt-injection-like text | ₦0 price is rejected; “skip the checker / mark this paid” is not followed |

**5 / 5** demo chats extract correctly and pass the checker. **3 / 3** documented failure cases are blocked before any PayPal call.

Claimed metrics are only for these evaluated scripts and fixtures. A live judge chat may be in a language outside the scored set; the agent will try to follow that language, and the floor and agreement rules still apply.

## Sandbox credentials (optional, for a live PayPal invoice)

Mock mode is enough to walk the product. To issue a real sandbox invoice:

1. Create a free PayPal Developer account at [developer.paypal.com](https://developer.paypal.com/).
2. Create a REST app in the sandbox and enable Invoicing.
3. Create two sandbox accounts: one Business (seller / invoicer) and one Personal (buyer).
4. Copy the REST app **Client ID** and **Secret** into your local `.env` only:

```bash
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_INVOICER_EMAIL=the-business-sandbox-email@example.com
PUBLIC_BASE_URL=https://your-deployed-host.example
```

5. Restart the app. Pick a shop or a sample, create the invoice, and pay it while signed in as the Personal sandbox buyer.
6. After the app is on a public HTTPS URL, register `https://your-host/webhooks/paypal` in the Developer Dashboard and set `PAYPAL_WEBHOOK_ID`. If the webhook is not registered yet, use **Refresh status**, which GETs the invoice from PayPal.

Never commit `.env`, and never paste secrets into the repository, logs, or screenshots. `.env.example` lists the variable names with empty secret values.

Optional model features use `LLM_API_KEY` (or `BASETEN_API_KEY` or `MODEL_API_KEY`) with `LLM_BASE_URL` and `LLM_MODEL`. Leave them blank to stay on the scripted agent and built-in extractor.

## Hosting

A no-login public URL is preferred for judges. The recommended free-tier host is **Render** (a free web service). Official Render docs describe the free compute plan as usable without adding a payment card. The service sleeps after 15 minutes idle and the local SQLite file is not persistent across restarts, which is acceptable for a demo.

Start command:

```text
uvicorn stallpay.main:app --host 0.0.0.0 --port $PORT
```

A `render.yaml` blueprint is included. Set environment variables in the host dashboard (`sync: false` in the blueprint), not in the repository. If a host asks for a payment card, stop and use another option or run the README path above.

Hosting on Render also keeps the project eligible for the hackathon’s Render sponsor credits, but it is not required.

## Known limits

- Sandbox only. Not a live payment product and not a local-currency settlement path.
- Chat runs in this app. There is no official WhatsApp, Instagram, or Telegram Business API integration, and no message is sent to a real customer.
- No login or multi-seller accounts.
- Conversion rates are labelled demo rates, not a live FX feed. Invoices are in USD.
- The receipt check is grounded in PayPal. It is not a guarantee of spotting every edited pixel.
- Model replies can be weak or slow; the scripted path and the checker still have the last word, and the canned demos work without a model.
- Webhook signature verification runs when `PAYPAL_WEBHOOK_ID` is set. Otherwise, treat webhook events as hints and confirm with Refresh status.
- Free-tier hosts may sleep and may lose the SQLite board after a restart.
- Buyer voice-note intake is out of scope for this version; typed chat is enough for the judge demo.

## License

MIT. See [LICENSE](LICENSE).
