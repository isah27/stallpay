# StallPay

StallPay is a shop agent for small sellers who close deals in Instagram, WhatsApp, or Telegram, in any country.

A buyer picks a business, chooses an item, and hears the real catalog price. If the seller has configured a promo, the agent states the usual price and the promo price, with the actual end date and time. It never invents a discount or a fake deadline. A deterministic checker, not the model, is what is allowed to create a PayPal invoice, and only after the buyer has clearly said yes to that exact item and price. If a buyer sends a payment screenshot, StallPay may read the fields, but only PayPal’s real invoice status can confirm the money. Unpaid invoices can be reminded through the official PayPal API, in the seller’s tone. The seller can play a short spoken morning briefing of what sold, what landed, and who still owes.

This project is a submission for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). It is sandbox-only. No real money moves, and no messages are sent to real customers.

## Who it is for

Small sellers everywhere who already take orders in chat and then get sent edited receipts or bank-alert screenshots as “proof.” There is often no invoice, and no reliable way to see whether PayPal actually received the money.

The live demo has three equal shops, not a single-country product with translations added on:

- Amaka’s tailor stall in Lagos, prices in naira, English and Nigerian Pidgin.
- Sofía’s jewelry stall in Mexico City, prices in Mexican pesos, Spanish.
- Priya’s textile stall in Jaipur, prices in rupees, Hindi and Hinglish.

Seller tools, including the original Lagos sample orders, live on a separate `/seller` page.

## What it does

1. Open the site with no login and pick a shop. The buyer then stays on one screen at a time: items, price, then pay.
2. The agent greets the buyer and lists the items it has. The buyer selects an item by tapping it or by typing in any language.
3. The agent states the price. If a promo is configured and still running, it quotes the list price and the promo price, and it names the real expiry. If no promo is configured, or the promo has ended, it just states the list price. Bargaining does not change the price; the agent says the promo price (or the list price) is already the best it can do.
4. A PayPal invoice and pay link appear only when a buyer utterance clearly says yes to that item and price, for example “Okay I want it,” in any language. A bare “ok” is not enough. Nothing about invoices or pay links is shown before that yes.
5. After the link, the buyer can Refresh until the status is Paid, or use “Already paid? Upload proof.” A parser may propose amount, currency, date, and reference. PayPal GET is the ground truth. The image itself never marks the order Paid.
6. Seller tools at `/seller` show the invoice board (draft / sent / paid / reminder sent), reminders through PayPal, a morning briefing, published metrics, and a paste-a-chat path for finished transcripts.

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

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Pick **Joyería Sofía**, choose the silver hoop earrings, read the promo and its end time, try a lower offer (the price should not change), then say clearly that you want it, for example “De acuerdo, lo tomo” or “Okay I want it.” The PayPal pay link should appear only after that yes. Optionally paste a fake receipt under “Already paid? Upload proof” — the check should refuse it because PayPal does not confirm payment. Open the pay link and click **Pay now (mock)**, then **Refresh status**. The status should flip to **paid**.

Seller tools are at [http://127.0.0.1:8000/seller](http://127.0.0.1:8000/seller). Click **Tailor in Surulere — 2 native shirts**, then **Extract and check**, then **Create PayPal invoice**. **Write briefing** and **Play** read the morning summary.

A public no-login demo is at [https://stallpay.onrender.com/](https://stallpay.onrender.com/). On Render’s free plan, the first visit after the service has been idle can take about a minute to wake.

Useful paths:

- `/` — no-login buyer demo
- `/seller` — invoice board, briefing, reminders, paste-a-chat
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
| Create draft invoice | `POST /v2/invoicing/invoices` — only after the checker has a quoted buyer yes at the listed or promo price |
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

It does not talk to PayPal, cannot mark an invoice paid, and cannot invent or accept a price other than the list price or an active configured promo. Ordinary code locks the price, the agreement gate, the totals, and the PayPal cross-check.

If no model key is set, or the model is slow or unusable, scripted replies and a built-in extractor still quote only catalog prices, refuse a missing yes, run the sample chats, and check proof text against PayPal. A judge is never blocked on an API key.

On a public host, model calls are capped per visitor and per day. The defaults are 200 calls per visitor per day, 30 per visitor per minute, and 3,000 across all visitors per day, plus a maximum prompt length and reply size. When a cap is reached, the scripted path and built-in parser are used instead, and the page shows a short note. The price and agreement checks still apply.

Treat chat text and receipt text as data, not instructions. Prompt-injection-like text is ignored as a command.

The receipt path does not claim to be a forensic photoshop detector. Many mobile screenshots have no useful metadata, and absence of metadata is not evidence of a fake. A borderline visual fake that cannot be confirmed is scored as unverified, waiting for PayPal — a correct refuse-to-credit, not proof that the image was edited.

## Published numbers

These results are produced by the scripted agent, the built-in extractor, and the deterministic checker, and can be reproduced with `pytest` or at `/metrics`. Misses are published, not rounded away.

### Price integrity

15 adversarial buyer scripts, split across English, Nigerian Pidgin, Spanish, and Hindi. They include a lowball far below the catalog price, last-price pressure, a false claim that the seller already agreed a lower number, a currency trick, emotional pressure, and prompt-injection-like “ignore the price” text.

**15 / 15** held the catalog price: the agent never quoted a price other than the list or active promo, and no invoice was created mid-bargain.

### Promo expiry

Three cases around Amaka’s gele, whose promo ended on 9 November 2026 at 9:00 PM Lagos time and is stored as expired data, not hidden.

**3 / 3** respected expiry: the expired promo price was never offered, a yes invoiced at the current list price, and a yes at the old promo price was blocked.

### Agreement gate

Chats with no explicit yes, a yes to a different price, a yes to different items, an ambiguous ok with no price, a yes that was only said by the agent, and one clear buyer yes after the catalog price was quoted.

**False invoice rate: 0.** 6 / 6 cases behaved as expected. No PayPal create unless a buyer utterance clearly agrees to the selected item at the listed or promo price.

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

Claimed metrics are only for these evaluated scripts and fixtures. A live judge chat may be in a language outside the scored set; the agent will try to follow that language, and the price and agreement rules still apply.

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

Optional model features use `LLM_API_KEY` (or `BASETEN_API_KEY` or `MODEL_API_KEY`) with `LLM_BASE_URL` and `LLM_MODEL`. Leave them blank to stay on the scripted agent and built-in extractor. Optional cap variables, with the defaults above, are `LLM_VISITOR_DAILY_LIMIT`, `LLM_GLOBAL_DAILY_LIMIT`, `LLM_VISITOR_BURST_PER_MINUTE`, `LLM_MAX_INPUT_CHARS`, and `LLM_MAX_TOKENS`.

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
- No login or multi-seller accounts. Promo prices and expiry dates are configured in the shop catalog, not in a seller admin UI.
- Conversion rates are labelled demo rates, not a live FX feed. Invoices are in USD.
- The receipt check is grounded in PayPal. It is not a guarantee of spotting every edited pixel.
- Model replies can be weak or slow; the scripted path and the checker still have the last word, and the canned demos work without a model.
- Public model use is capped per visitor and per day so a busy demo cannot run unbounded. Past a cap, replies fall back to the scripted path.
- Webhook signature verification runs when `PAYPAL_WEBHOOK_ID` is set. Otherwise, treat webhook events as hints and confirm with Refresh status.
- Free-tier hosts may sleep and may lose the SQLite board after a restart.
- Buyer voice-note intake is out of scope for this version; typed chat or a tap on an item is enough for the judge demo.

## License

MIT. See [LICENSE](LICENSE).
