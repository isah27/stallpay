const viewShops = document.getElementById('view-shops');
const viewChat = document.getElementById('view-chat');
const threadEl = document.getElementById('thread');
const chatForm = document.getElementById('chat-form');
const buyerInput = document.getElementById('buyer-input');
const sendChatBtn = document.getElementById('send-chat-btn');
const dealStatus = document.getElementById('deal-status');
const itemChips = document.getElementById('item-chips');
const shopTitle = document.getElementById('shop-title');
const shopSub = document.getElementById('shop-sub');
const payCard = document.getElementById('pay-card');
const paySummary = document.getElementById('pay-summary');
const payLink = document.getElementById('pay-link');
const payStatus = document.getElementById('pay-status');
const refreshBtn = document.getElementById('refresh-btn');
const proofText = document.getElementById('proof-text');
const proofFile = document.getElementById('proof-file');
const proofBtn = document.getElementById('proof-btn');
const proofResult = document.getElementById('proof-result');

let session = null;

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function showUsageNote(note) {
  const el = document.getElementById('usage-note');
  if (!el) return;
  if (note) {
    el.textContent = note;
    el.classList.remove('hidden');
  } else {
    el.textContent = '';
    el.classList.add('hidden');
  }
}

function setStep(name) {
  document.querySelectorAll('.step').forEach((el) => {
    el.classList.toggle('current', el.dataset.step === name);
  });
}

function showShops() {
  session = null;
  viewShops.classList.remove('hidden');
  viewChat.classList.add('hidden');
  payCard.classList.add('hidden');
  dealStatus.textContent = '';
  showUsageNote('');
  setStep('shop');
  document.querySelectorAll('.shop-card').forEach((card) => card.classList.remove('active'));
}

function renderThread(messages) {
  threadEl.innerHTML = (messages || [])
    .map((m) => {
      const who = m.role === 'seller' ? 'Seller' : 'You (buyer)';
      return (
        '<div class="bubble ' + m.role + '"><span class="who">' + who + '</span>' +
        escapeHtml(m.text) + '</div>'
      );
    })
    .join('');
  threadEl.scrollTop = threadEl.scrollHeight;
}

function renderChips(shop, selectedIds) {
  const items = (shop && shop.items) || [];
  if (!items.length) {
    itemChips.hidden = true;
    itemChips.innerHTML = '';
    return;
  }
  itemChips.hidden = false;
  itemChips.innerHTML = items
    .map((item) => {
      const selected = (selectedIds || []).includes(item.id) ? ' active' : '';
      return (
        '<button type="button" class="chip' + selected + '" data-item="' + escapeHtml(item.id) + '">' +
        escapeHtml(item.name) + '</button>'
      );
    })
    .join('');
}

function renderPay(sess) {
  if (!sess || !sess.pay_url) {
    payCard.classList.add('hidden');
    return;
  }
  payCard.classList.remove('hidden');
  const price = sess.quoted_price_display || '';
  const names = (sess.items || []).map((item) => item.name).join(', ');
  paySummary.textContent = (names || 'Your item') + (price ? ' · ' + price : '');
  payLink.href = sess.pay_url;
  payStatus.textContent = sess.invoice_status
    ? 'Status: ' + sess.invoice_status + (sess.paypal_invoice_id ? ' · ' + sess.paypal_invoice_id : '')
    : '';
}

function renderSession(sess, extra) {
  session = sess;
  if (!sess) return;
  const shop = sess.shop;
  shopTitle.textContent = shop.name;
  shopSub.textContent = shop.city + ', ' + shop.country + ' · ' + shop.seller_name;
  renderThread(sess.messages);
  renderChips(shop, (sess.items || []).map((item) => item.id));
  setStep(sess.stage === 'agreed' || sess.stage === 'pay' ? (sess.pay_url ? 'pay' : 'price') : sess.stage || 'item');
  if (sess.pay_url) {
    setStep('pay');
    dealStatus.textContent = '';
  } else if (sess.quoted_price_display && !sess.agreement_quote) {
    dealStatus.textContent = '';
  }
  if (extra && extra.reason && !extra.invoiced) {
    dealStatus.textContent = extra.reason;
  }
  renderPay(sess);
}

async function startShop(shopId) {
  document.querySelectorAll('.shop-card').forEach((card) => {
    card.classList.toggle('active', card.dataset.shop === shopId);
  });
  const res = await fetch('/api/chats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ shop_id: shopId }),
  });
  const data = await res.json();
  if (!res.ok) {
    dealStatus.textContent = data.detail || 'Could not start the chat.';
    return;
  }
  viewShops.classList.add('hidden');
  viewChat.classList.remove('hidden');
  payCard.classList.add('hidden');
  proofResult.innerHTML = '';
  showUsageNote('');
  renderSession(data);
  buyerInput.disabled = false;
  sendChatBtn.disabled = false;
  buyerInput.focus();
}

async function sendBuyer(payload) {
  if (!session) return;
  sendChatBtn.disabled = true;
  try {
    const res = await fetch('/api/chats/' + session.id + '/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      dealStatus.textContent = data.detail || 'The message could not be sent.';
      return;
    }
    showUsageNote(data.usage_note);
    renderSession(data.session, data);
  } finally {
    sendChatBtn.disabled = false;
    buyerInput.focus();
  }
}

document.querySelectorAll('.shop-card').forEach((card) => {
  card.addEventListener('click', () => startShop(card.dataset.shop));
});

document.getElementById('change-shop-btn').addEventListener('click', showShops);

itemChips.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-item]');
  if (!button || !session) return;
  sendBuyer({ item_id: button.dataset.item });
});

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = buyerInput.value.trim();
  if (!text || !session) return;
  buyerInput.value = '';
  await sendBuyer({ text });
});

refreshBtn.addEventListener('click', async () => {
  if (!session || !session.invoice_pk) return;
  refreshBtn.disabled = true;
  try {
    const res = await fetch('/api/invoices/' + session.invoice_pk + '/refresh', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      payStatus.textContent = data.detail || 'Could not refresh the invoice.';
      return;
    }
    session.invoice_status = data.status;
    payStatus.textContent = 'Status: ' + data.status + (data.paypal_invoice_id ? ' · ' + data.paypal_invoice_id : '');
  } finally {
    refreshBtn.disabled = false;
  }
});

proofBtn.addEventListener('click', async () => {
  if (!session || !session.invoice_pk) {
    proofResult.innerHTML = '<p class="hint">The pay link appears after you say yes. Then you can upload proof.</p>';
    return;
  }
  proofBtn.disabled = true;
  try {
    const file = proofFile.files && proofFile.files[0];
    let res;
    if (file) {
      const body = new FormData();
      body.append('text', proofText.value);
      body.append('image', file);
      res = await fetch('/api/invoices/' + session.invoice_pk + '/proof', { method: 'POST', body });
    } else {
      res = await fetch('/api/invoices/' + session.invoice_pk + '/proof', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: proofText.value }),
      });
    }
    const data = await res.json();
    if (!res.ok) {
      proofResult.innerHTML = '<div class="verdict amount_or_reference_mismatch">' + escapeHtml(data.detail || 'Check failed') + '</div>';
      return;
    }
    const reasons = (data.reasons || []).map((r) => '<li>' + escapeHtml(r) + '</li>').join('');
    const usage = data.usage_note
      ? '<p class="hint usage-note">' + escapeHtml(data.usage_note) + '</p>'
      : '';
    proofResult.innerHTML =
      '<div class="verdict ' + escapeHtml(data.verdict) + '"><strong>' + escapeHtml(data.summary) + '</strong>' +
      '<p>PayPal status: ' + escapeHtml(data.paypal_status || 'unknown') +
      (data.paypal_amount_usd ? ' · $' + escapeHtml(data.paypal_amount_usd) : '') +
      '</p><ul>' + reasons + '</ul>' +
      '<p class="hint">This result does not mark the order paid by itself. Use Refresh status after a real payment.</p>' +
      usage + '</div>';
  } finally {
    proofBtn.disabled = false;
  }
});
