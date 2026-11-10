# StallPay demo video script

Hard cap: 2 minutes 45 seconds (under the 3-minute limit). No copyrighted music. No PayPal logo misuse beyond showing the actual sandbox checkout. Film the desktop browser so the host URL is visible. Upload to the Isah Neziru Dev YouTube channel as Public when the recording is approved. This file is a script only; nothing has been recorded yet.

## 0:00–0:20 — The job

On screen: quick cuts of chat-style orders in Spanish, English or Pidgin, and Hindi, then the StallPay URL with no login.

Say: “Small sellers close deals in Instagram, WhatsApp, and Telegram in every country. They haggle, they get sent fake payment screenshots, and they have no invoice they can trust.”

## 0:20–1:20 — Hold the floor, take a real yes, invoice, paid

On screen: Joyería Sofía. The buyer asks for the silver hoop earrings, offers a price below the floor, and the agent holds. The buyer then agrees in Spanish at the legal price, including the exact amount. The checker shows the quoted yes and the floor check. A PayPal sandbox invoice is created. The Personal sandbox buyer pays. The board flips to Paid.

Say: “Watch it hold the floor, take a real yes in the buyer’s own words, and only then create the PayPal invoice. When the buyer actually pays, the board flips to Paid.”

## 1:20–2:10 — Fake receipt refused

On screen: Amaka’s Lagos stall or Priya’s Jaipur stall. Start or reuse an unpaid invoice. The buyer pastes or uploads a fake receipt. The proof panel shows PayPal status and the mismatch. The board does not show Paid.

Say: “This looks like a payment alert, but PayPal says the invoice is not paid, so the agent refuses it.”

## 2:10–2:30 — Morning briefing

On screen: seller view. Click Write briefing and Play, so the spoken summary is heard. If speech is unavailable in the recording setup, leave the written briefing on screen and say the same lines.

Say: “In the morning the seller gets a short spoken briefing: what closed, what landed, who still owes.”

## 2:30–2:45 — Limits and numbers

On screen: the /metrics tables, with the URL still visible.

Say: “Sandbox only. Invoices are in USD with a labelled conversion from the seller’s currency. Chat runs in the app, not on the official WhatsApp API. The receipt check is grounded in PayPal, not a claim that every edited pixel can be spotted. Here are the published numbers, including any misses.”

Current numbers to show, reproducible with pytest: floor integrity 15/15, agreement-gate false invoices 0, payment-proof fakes caught 4/4, genuine proofs confirmed 1/1, v1 regression 5/5 extract-and-pass and 3/3 failures blocked.
