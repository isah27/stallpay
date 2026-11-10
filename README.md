# StallPay

StallPay turns a pasted WhatsApp order into a checked PayPal invoice.

It is built for informal Nigerian sellers — tailors, food vendors, freelancers, phone-accessory stalls — who close deals in chat and then chase payment with account numbers. There is no invoice, no receipt, and no reliable way to see who has paid. StallPay extracts the line items, a deterministic checker signs off the quantities and totals, and PayPal creates a sandbox invoice with a pay link. When the buyer pays, a webhook (or a Refresh status button) marks the order paid. The seller can send one official PayPal reminder for an unpaid invoice.

This project is a submission for the [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/). It is sandbox-only. No real money moves, and no messages are sent to real customers.

## Who it is for

Nigerian sellers who already take orders on WhatsApp and need a payment record they can trust.

## What it does

1. You paste a chat, or click one of five canned Nigerian orders.
2. An extractor proposes buyer name, email, line items, and a stated naira total.
3. A code checker validates the email, quantities, line totals, and a labelled naira-to-USD conversion. If the check fails, PayPal is not called.
4. On a passing draft, StallPay creates and sends a PayPal invoice in **USD**. The UI still shows the original naira prices and the conversion rate printed on the invoice notes.
5. The board shows draft / sent / paid / reminder sent. A pay link opens the PayPal payer view (or a mock payer page when credentials are not configured).
6. A `/webhooks/paypal` endpoint updates the board when PayPal reports payment. A Refresh status button also GETs the invoice, so a missed webhook does not block the demo.

## Clone and run (mock mode, no keys required)

You need Python 3.11 or newer.

```bash
git clone <this-repository-url>
cd stallpay
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # leave PAYPAL_MODE=mock
uvicorn stallpay.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Click **Tailor in Surulere — 2 native shirts**, then **Extract and check**, then **Create PayPal invoice**. Open the pay link and click **Pay now (mock)**. The board should flip to **paid**. Optionally click **Send reminder** on a new unpaid invoice.

Useful paths:

- `/` — no-login demo
- `/health` — liveness
- `/metrics` — published accuracy table
- `/webhooks/paypal` — PayPal webhook receiver
- `/mock-pay/{invoice_id}` — mock payer page (mock mode only)

Run the tests:

```bash
pytest -q
```

## How PayPal is used

StallPay calls the PayPal sandbox Invoicing API:

| Step | API |
| --- | --- |
| Create draft invoice | `POST /v2/invoicing/invoices` |
| Send invoice (pay link, no recipient email) | `POST /v2/invoicing/invoices/{id}/send` with `send_to_recipient: false` |
| Read status | `GET /v2/invoicing/invoices/{id}` |
| Remind an unpaid buyer | `POST /v2/invoicing/invoices/{id}/remind` |
| Payment updates | Webhooks on invoice paid / cancelled / refunded, plus a manual refresh |

The invoice is always issued in USD. NGN is shown in the UI and in the invoice note, using a fixed, dated demo rate (`1 USD = 1,480.00 NGN` as of 10 November 2026, overridable with `NGN_PER_USD` and `RATE_AS_OF`). This avoids depending on NGN being a usable sandbox invoice currency.

Recipient emails are not sent automatically when an invoice is created, so a pasted real-world address is not contacted. Use sandbox or `@example.com` addresses only.

## How AI is used

The model, when a key is configured, has one job: propose a structured order from messy chat English and Pidgin-tinged messages. It does not talk to PayPal and it cannot mark an invoice paid. The checker is ordinary code.

If no model key is set, a built-in heuristic extractor still handles the five canned demo chats, so a judge can run the product without an LLM account.

Treat the pasted chat as data, not instructions. Prompt-injection-like text is ignored as a command and is documented as a blocked failure case.

## Published numbers

These results are produced by the built-in extractor and the checker, and can be reproduced with `pytest` or at `/metrics`.

| Sample | Result |
| --- | --- |
| Tailor in Surulere — 2 native shirts | Extracts correctly, checker passes |
| Food stall — jollof and grilled fish | Extracts correctly, checker passes |
| Freelancer — logo and social templates | Extracts correctly, checker passes |
| Phone accessories — protectors and power bank | Extracts correctly, checker passes |
| Mixed Pidgin/English — Ankara and gele | Extracts correctly, checker passes |
| Failure: missing price | Checker blocks the PayPal call |
| Failure: stated total does not match | Lines extract, checker blocks the ₦25,000 vs ₦30,000 mismatch |
| Failure: prompt-injection-like text | ₦0 price is rejected; "skip the checker / mark this paid" is not followed |

**5 / 5** demo chats extract correctly and pass the checker. **3 / 3** documented failure cases are blocked before any PayPal call.

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

5. Restart the app. Click a sample, create the invoice, and pay it while signed in as the Personal sandbox buyer.
6. After the app is on a public HTTPS URL, register `https://your-host/webhooks/paypal` in the Developer Dashboard and set `PAYPAL_WEBHOOK_ID`. If the webhook is not registered yet, use **Refresh status**, which GETs the invoice from PayPal.

Never commit `.env`, and never paste secrets into the repository, logs, or screenshots. `.env.example` lists the variable names with empty secret values.

Optional model extraction uses `LLM_API_KEY` (or `BASETEN_API_KEY`) with `LLM_BASE_URL` and `LLM_MODEL`. Leave them blank to stay on the built-in extractor.

## Hosting

A no-login public URL is preferred for judges. The recommended free-tier host is **Render** (a free web service). Official Render docs describe the free compute plan as usable without adding a payment card. The service sleeps after 15 minutes idle and the local SQLite file is not persistent across restarts, which is acceptable for a demo.

Start command:

```text
uvicorn stallpay.main:app --host 0.0.0.0 --port $PORT
```

Set the same environment variables in the host dashboard, not in the repository. If a host asks for a payment card, stop and use another option or run the README path above. Fly.io is not recommended for a new account because it no longer has a no-card free tier.

A `render.yaml` blueprint is included. Hosting on Render also keeps the project eligible for the hackathon's Render sponsor credits, but it is not required.

## Known limits

- Sandbox only. Not a live payment product and not a naira settlement path.
- No WhatsApp Business API. The seller pastes the chat.
- No login or multi-seller accounts.
- The conversion rate is a labelled demo rate, not a live FX feed.
- Model extraction can fail on messy chats; the checker still has the last word, and the five demos work without a model.
- Webhook signature verification runs when `PAYPAL_WEBHOOK_ID` is set. Otherwise, treat webhook events as hints and confirm with Refresh status.
- Free-tier hosts may sleep and may lose the SQLite board after a restart.

## License

MIT. See [LICENSE](LICENSE).
