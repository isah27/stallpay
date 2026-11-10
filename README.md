# StallPay

StallPay is a shop agent for small sellers who close deals in Instagram, WhatsApp, or Telegram, in any country.

A buyer picks a business, chooses an item, and hears the real catalog price. If the seller has configured a promo, the agent states the usual price and the promo price, with the actual end date and time. It never invents a discount or a fake deadline. A deterministic checker, not the model, is what is allowed to create a PayPal invoice, and only after the buyer has clearly said yes to that exact item and price. If a buyer sends a payment screenshot, StallPay may read the fields, but only PayPal’s real invoice status can confirm the money. Unpaid invoices can be reminded through the official PayPal API, in the seller’s tone. The seller can play a short spoken morning briefing of what sold, what landed, and who still owes.

This project is a submission for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). It is sandbox-only. No real money moves, and no messages are sent to real customers.

## Who it is for

Small sellers everywhere who already take orders in chat and then get sent edited receipts or bank-alert screenshots as “proof.” There is often no invoice, and no reliable way to see whether PayPal actually received the money.

The live demo has three equal shops, all in English unless the buyer picks another language:

- Amaka’s tailor stall in Lagos, prices in naira.
- Sofía’s jewelry stall in Mexico City, prices in Mexican pesos.
- Priya’s textile stall in Jaipur, prices in rupees.

A small language picker at the top of the buyer page offers English, Español, हिन्दी, Pidgin, and Français. That choice changes the greeting, item list, prices and promo text, replies, and the pay step, and it stays for the session. If the buyer types in another language without picking one, the agent still understands them, but it keeps replying in English.

Seller tools, including the original Lagos sample orders, live on a separate `/seller` page.

## What it does

1. Open the site with no login and pick a shop. The buyer page is a clean shop chat in English: no step labels, no conversion rates, and no developer notes. Prices are shown in the shop’s own currency. Use the language picker if you want the shop in Español, हिन्दी, Pidgin, or Français.
2. The agent greets the buyer in the selected language and lists the items it has. The buyer selects an item by tapping it, by typing a name in English or a local name, or by saying “1” or “the first one.”
3. The agent states the price. If a promo is configured and still running, it quotes the list price and the promo price, and it names the real expiry. If no promo is configured, or the promo has ended, it just states the list price. Bargaining does not change the price; the agent says the promo price (or the list price) is already the best it can do.
4. A PayPal invoice is created only when a buyer utterance clearly says yes to that item and price, for example “Okay I want it,” including in Spanish, Hindi, Pidgin, or French. A bare “ok” is not enough. Nothing about invoices or pay links is shown before that yes.
5. After that yes, the chat is hidden. The buyer sees only an order summary (shop, item, quantity, list price, any promo discount with its real end time, the total in the shop’s currency, the USD amount the PayPal invoice is billed in, and the invoice number), a gold “Proceed with PayPal” button, and “I’ve already paid.” “I’ve already paid” checks the invoice with PayPal’s GET invoice API. If the status is PAID or MARKED_AS_PAID, the page shows a confirmation. Otherwise it says PayPal has not confirmed payment yet and keeps both buttons. There is no receipt or proof upload. PayPal’s status is the only way payment is confirmed.
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

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The first line is “Select the shop you want to buy from.” The shop is in English unless you change the language picker. Pick **Joyería Sofía**, choose the silver hoop earrings, read the promo and its end time, try a lower offer (the price should not change), then say clearly that you want it, for example “Okay I want it.” Your messages appear in the chat immediately. After that yes, the chat is replaced by the order summary. Click **I’ve already paid** before paying — it should say PayPal has not confirmed payment yet. Then click **Proceed with PayPal**, complete payment (in mock mode, click **Pay now (mock)**), and click **I’ve already paid** again. The page should show that PayPal has confirmed the payment.

Seller tools are at [http://127.0.0.1:8000/seller](http://127.0.0.1:8000/seller). Click **Tailor in Surulere — 2 native shirts**, then **Extract and check**, then **Create PayPal invoice**. **Write briefing** and **Play** read the morning summary.

A public no-login demo is at [https://stallpay.onrender.com/](https://stallpay.onrender.com/). On Render’s free plan, the first visit after the service has been idle can take about a minute to wake.

Useful paths:

- `/` — no-login buyer shop chat
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
| Read status | `GET /v2/invoicing/invoices/{id}` — board, and the buyer’s “I’ve already paid” check |
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

- draft a reply to a free-text buyer message (item picks and price quotes are scripted and return immediately)
- propose structured fields from a pasted or finished chat
- draft reminder copy and the morning briefing

It does not talk to PayPal, cannot mark an invoice paid, and cannot invent or accept a price other than the list price or an active configured promo. Ordinary code locks the price, the agreement gate, the totals, and the PayPal cross-check.

If no model key is set, or the model is slow or unusable, scripted replies and a built-in extractor still quote only catalog prices, refuse a missing yes, and run the sample chats. Item selection and price quotes never wait on the model. Free-text turns wait a few seconds for a model reply, then fall back to the scripted agent. A judge is never blocked on an API key. Payment is confirmed only by PayPal’s invoice status, not by a receipt image or pasted text.

On a public host, model calls are capped per visitor and per day. The defaults are 200 calls per visitor per day, 30 per visitor per minute, and 3,000 across all visitors per day, plus a maximum prompt length and reply size. When a cap is reached, the scripted path and built-in parser are used instead, and the page shows a short note. The price and agreement checks still apply.

Treat chat text and receipt text as data, not instructions. Prompt-injection-like text is ignored as a command.

## Published numbers

These results are produced by the scripted agent, the built-in extractor, and the deterministic checker, and can be reproduced with `pytest` or at `/metrics`. Misses are published, not rounded away.

### Price integrity

15 adversarial buyer scripts, with English as the default shop language and buyer messages in English, Nigerian Pidgin, Spanish, and Hindi. They include a lowball far below the catalog price, last-price pressure, a false claim that the seller already agreed a lower number, a currency trick, emotional pressure, and prompt-injection-like “ignore the price” text.

**15 / 15** held the catalog price: the agent never quoted a price other than the list or active promo, and no invoice was created mid-bargain.

### Promo expiry

Three cases around Amaka’s gele, whose promo ended on 9 November 2026 at 9:00 PM Lagos time and is stored as expired data, not hidden.

**3 / 3** respected expiry: the expired promo price was never offered, a yes invoiced at the current list price, and a yes at the old promo price was blocked.

### Agreement gate

Chats with no explicit yes, a yes to a different price, a yes to different items, an ambiguous ok with no price, a yes that was only said by the agent, and one clear buyer yes after the catalog price was quoted.

**False invoice rate: 0.** 6 / 6 cases behaved as expected. No PayPal create unless a buyer utterance clearly agrees to the selected item at the listed or promo price.

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

Claimed metrics are only for these evaluated scripts and fixtures. Shops stay in English unless the buyer picks another language. A live judge can type in another language without picking one; the agent should still understand the request, keep replying in English, and apply the same price and agreement rules.

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

Optional model features use `LLM_API_KEY` (or `BASETEN_API_KEY` or `MODEL_API_KEY`) with `LLM_BASE_URL` and `LLM_MODEL`. Leave them blank to stay on the scripted agent and built-in extractor. Optional cap variables, with the defaults above, are `LLM_VISITOR_DAILY_LIMIT`, `LLM_GLOBAL_DAILY_LIMIT`, `LLM_VISITOR_BURST_PER_MINUTE`, `LLM_MAX_INPUT_CHARS`, `LLM_MAX_TOKENS`, and `LLM_CHAT_TIMEOUT` (default 4.5 seconds).

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
- Model replies can be weak or slow; item picks and quotes skip the model, free-text turns time out after a few seconds, and the scripted path and the checker still have the last word.
- Public model use is capped per visitor and per day so a busy demo cannot run unbounded. Past a cap, replies fall back to the scripted path.
- Webhook signature verification runs when `PAYPAL_WEBHOOK_ID` is set. Otherwise, treat webhook events as hints and confirm with Refresh status.
- Free-tier hosts may sleep and may lose the SQLite board after a restart.
- Buyer voice-note intake is out of scope for this version; typed chat or a tap on an item is enough for the judge demo.

## License

MIT. See [LICENSE](LICENSE).
