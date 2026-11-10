# StallPay demo video script

Hard cap: 2 minutes 45 seconds (under the 3-minute limit). No copyrighted music. No PayPal logo misuse beyond showing the actual sandbox checkout. Film the desktop browser so the host URL is visible. Upload to the Isah Neziru Dev YouTube channel as Public when the recording is approved. This file is a script only; nothing has been recorded yet.

## 0:00–0:20 — The job

On screen: quick cuts of chat-style orders in Spanish, English or Pidgin, and Hindi, then the StallPay URL with no login.

Say: “Small sellers close deals in Instagram, WhatsApp, and Telegram in every country. Buyers ask the price, they try to bargain, and they send fake payment screenshots. Sellers need a real invoice they can trust.”

## 0:20–1:20 — Pick a shop, hear the promo, say yes, paid

On screen: the step-by-step buyer flow at the live URL. Pick Joyería Sofía. The agent greets and lists the items, with no pay link yet. Choose the silver hoop earrings. The agent states the list price and the configured promo, including the real end time. The buyer tries to bargain it down; the agent holds the promo price as the best price. The buyer says clearly, in Spanish, that they want it. Only then does the PayPal sandbox invoice and pay link appear. The Personal sandbox buyer pays. Refresh shows Paid.

Say: “Watch it walk one step at a time. The price is the seller’s real promo, not a made-up bargain. A PayPal invoice appears only after a clear yes. When the buyer actually pays, the status flips to Paid.”

## 1:20–2:10 — Fake receipt refused

On screen: Amaka’s Lagos stall or Priya’s Jaipur stall, after a pay link exists. The buyer pastes or uploads a fake receipt under “Already paid? Upload proof.” The panel shows PayPal status and the mismatch. Refresh still does not show Paid.

Say: “This looks like a payment alert, but PayPal says the invoice is not paid, so the agent refuses it.”

## 2:10–2:30 — Seller tools and morning briefing

On screen: open the discreet Seller tools link. Click Write briefing and Play, so the spoken summary is heard. If speech is unavailable in the recording setup, leave the written briefing on screen and say the same lines.

Say: “Sellers get the invoice board, reminders, and a short spoken morning briefing: what closed, what landed, who still owes.”

## 2:30–2:45 — Limits and numbers

On screen: the /metrics tables, with the URL still visible.

Say: “Sandbox only. Invoices are in USD with a labelled conversion from the seller’s currency. Chat runs in the app, not on the official WhatsApp API. The receipt check is grounded in PayPal, not a claim that every edited pixel can be spotted. Here are the published numbers, including any misses.”

Current numbers to show, reproducible with pytest: price integrity 15/15, promo expiry 3/3, agreement-gate false invoices 0, payment-proof fakes caught 4/4, genuine proofs confirmed 1/1, v1 regression 5/5 extract-and-pass and 3/3 failures blocked.
