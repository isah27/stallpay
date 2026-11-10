const chat = document.getElementById('chat');
const previewBtn = document.getElementById('preview-btn');
const recheckBtn = document.getElementById('recheck-btn');
const sendBtn = document.getElementById('send-btn');
const draftEmpty = document.getElementById('draft-empty');
const draftPanel = document.getElementById('draft-panel');
const checkBox = document.getElementById('check-box');
const linesBody = document.querySelector('#lines tbody');
const conversion = document.getElementById('conversion');
const sendStatus = document.getElementById('send-status');
const invoicesEl = document.getElementById('invoices');
const threadEl = document.getElementById('thread');
const chatForm = document.getElementById('chat-form');
const buyerInput = document.getElementById('buyer-input');
const sendChatBtn = document.getElementById('send-chat-btn');
const dealStatus = document.getElementById('deal-status');
const offerBox = document.getElementById('offer-box');
const invoiceBtn = document.getElementById('invoice-btn');
const invoiceStatus = document.getElementById('invoice-status');
const proofPanel = document.getElementById('proof-panel');
const proofText = document.getElementById('proof-text');
const proofFile = document.getElementById('proof-file');
const proofBtn = document.getElementById('proof-btn');
const proofResult = document.getElementById('proof-result');
const briefBtn = document.getElementById('brief-btn');
const speakBtn = document.getElementById('speak-btn');
const briefText = document.getElementById('brief-text');

let lastOrder = null;
let session = null;
let activeInvoiceId = null;
let briefingSpeech = '';

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


function bindSampleButtons() {
  document.querySelectorAll('.sample').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sample').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      chat.value = btn.dataset.text || '';
    });
  });
}

function readDraft() {
  const items = [];
  linesBody.querySelectorAll('tr').forEach((row) => {
    items.push({
      name: row.querySelector('.item-name').value,
      quantity: row.querySelector('.item-qty').value,
      unit_price_ngn: row.querySelector('.item-price').value,
    });
  });
  return {
    buyer_name: document.getElementById('buyer-name').value,
    buyer_email: document.getElementById('buyer-email').value,
    stated_total_ngn: document.getElementById('stated-total').value,
    currency: (lastOrder && lastOrder.currency) || 'NGN',
    items,
    raw_text: chat.value,
    source: (lastOrder && lastOrder.source) || 'manual',
    notes: (lastOrder && lastOrder.notes) || '',
  };
}

function renderDraft(data) {
  lastOrder = data.order;
  draftEmpty.classList.add('hidden');
  draftPanel.classList.remove('hidden');
  const check = data.check;
  checkBox.className = 'check-box ' + (check.ok ? 'ok' : 'bad');
  let html = check.ok
    ? '<strong>Checker passed.</strong> PayPal can be called with this draft.'
    : '<strong>Checker blocked this draft.</strong> No PayPal call will be made.';
  const msgs = []
    .concat(check.errors || [])
    .concat(check.warnings || []);
  if (msgs.length) {
    html += '<ul>' + msgs.map((m) => '<li>' + escapeHtml(m) + '</li>').join('') + '</ul>';
  }
  checkBox.innerHTML = html;
  document.getElementById('buyer-name').value = data.order.buyer_name || '';
  document.getElementById('buyer-email').value = data.order.buyer_email || '';
  document.getElementById('stated-total').value = data.order.stated_total_ngn || '';
  linesBody.innerHTML = '';
  (data.order.items || []).forEach((item) => {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td><input class="item-name" type="text"></td>' +
      '<td><input class="item-qty" type="text"></td>' +
      '<td><input class="item-price" type="text"></td>' +
      '<td class="line-total"></td>';
    tr.querySelector('.item-name').value = item.name || '';
    tr.querySelector('.item-qty').value = item.quantity || '';
    tr.querySelector('.item-price').value = item.unit_price_ngn || item.unit_price || '';
    tr.querySelector('.line-total').textContent = item.line_total_display || item.line_total_ngn_display || '';
    linesBody.appendChild(tr);
  });
  const currency = check.currency || data.order.currency || 'NGN';
  if (check.ok) {
    conversion.textContent =
      'PayPal will collect ' +
      check.usd_total_display +
      ' at 1 USD = ' +
      check.rate +
      ' ' +
      currency +
      ' (dated ' +
      check.rate_as_of +
      '). Original total ' +
      (check.computed_total_display || check.computed_total_ngn_display) +
      '.';
  } else {
    conversion.textContent = 'Fix the checker errors, then re-check before creating an invoice.';
  }
  sendBtn.disabled = !check.ok;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderInvoices(list) {
  if (!list.length) {
    invoicesEl.innerHTML = '<div class="empty">No invoices yet.</div>';
    return;
  }
  invoicesEl.innerHTML = list
    .map((inv) => {
      const closed = ['paid', 'cancelled', 'refunded'].includes(inv.status);
      const remind = closed
        ? ''
        : '<button type="button" class="remind" data-id="' + inv.id + '">Send reminder</button>';
      const useProof = '<button type="button" class="use-proof" data-id="' + inv.id + '">Use for proof</button>';
      const link = inv.pay_url
        ? '<p><a href="' + escapeHtml(inv.pay_url) + '" target="_blank" rel="noopener">Open pay link</a></p>'
        : '';
      const reminder = inv.reminder_sent ? '<p class="hint">Reminder sent</p>' : '';
      return (
        '<article class="invoice" data-id="' + inv.id + '">' +
        '<header><strong>' + escapeHtml(inv.buyer_name) + '</strong>' +
        '<span class="status status-' + escapeHtml(inv.status) + '">' + escapeHtml(inv.status) + '</span></header>' +
        '<p>' + escapeHtml(inv.buyer_email) + '</p>' +
        '<p class="mono">' + escapeHtml(inv.paypal_invoice_id || '') + '</p>' +
        link + reminder +
        '<div class="actions">' +
        '<button type="button" class="refresh" data-id="' + inv.id + '">Refresh status</button>' +
        remind + useProof +
        '</div></article>'
      );
    })
    .join('');
}

async function loadInvoices() {
  const res = await fetch('/api/invoices');
  const data = await res.json();
  renderInvoices(data);
}

async function runPreview(payload) {
  sendStatus.textContent = '';
  previewBtn.disabled = true;
  try {
    const res = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok && !data.order) {
      checkBox.className = 'check-box bad';
      draftEmpty.classList.add('hidden');
      draftPanel.classList.remove('hidden');
      checkBox.innerHTML = '<strong>Could not extract the order.</strong> ' + escapeHtml(data.detail || 'Try again.');
      return;
    }
    renderDraft(data);
  } finally {
    previewBtn.disabled = false;
  }
}

previewBtn.addEventListener('click', () => runPreview({ text: chat.value }));
recheckBtn.addEventListener('click', () => runPreview({ order: readDraft(), raw_text: chat.value }));

sendBtn.addEventListener('click', async () => {
  sendBtn.disabled = true;
  sendStatus.textContent = 'Creating invoice…';
  try {
    const res = await fetch('/api/invoices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order: readDraft(), raw_text: chat.value }),
    });
    const data = await res.json();
    if (data.ok) {
      sendStatus.textContent = 'Invoice sent. Open the pay link from the board.';
      renderDraft(data);
      await loadInvoices();
      if (data.invoice) selectProofInvoice(data.invoice.id);
    } else if (data.blocked) {
      sendStatus.textContent = 'Checker blocked the invoice.';
      renderDraft(data);
    } else {
      sendStatus.textContent = data.error || data.detail || 'PayPal request failed.';
    }
  } finally {
    sendBtn.disabled = false;
  }
});

invoicesEl.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  const id = button.dataset.id;
  if (button.classList.contains('use-proof')) {
    selectProofInvoice(id);
    return;
  }
  const isRemind = button.classList.contains('remind');
  const path = isRemind ? `/api/invoices/${id}/remind` : `/api/invoices/${id}/refresh`;
  button.disabled = true;
  try {
    const res = await fetch(path, { method: 'POST' });
    if (res.ok) {
      await loadInvoices();
    } else {
      const data = await res.json().catch(() => ({}));
      alert(data.detail || 'Request failed');
    }
  } finally {
    button.disabled = false;
  }
});

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

function renderOffer(sess) {
  session = sess;
  if (!sess) return;
  const bits = [];
  bits.push('<p><strong>' + escapeHtml(sess.shop.name) + '</strong> · ' + escapeHtml(sess.shop.currency) + '</p>');
  if (sess.current_offer_display) {
    bits.push('<p>Current offer: <strong>' + escapeHtml(sess.current_offer_display) + '</strong></p>');
  }
  if (sess.floor_total_display) {
    bits.push('<p>Floor: ' + escapeHtml(sess.floor_total_display) + ' ' + (sess.floor_held ? '(held)' : '(BROKEN)') + '</p>');
  }
  if (sess.agreement_quote) {
    bits.push('<p>Quoted buyer yes: “' + escapeHtml(sess.agreement_quote) + '”</p>');
  } else {
    bits.push('<p class="hint">No priced yes from the buyer yet. A bare “ok” is not enough.</p>');
  }
  if (sess.floor_events && sess.floor_events.length) {
    bits.push('<p class="hint">Below-floor attempts were rewritten ' + sess.floor_events.length + ' time(s).</p>');
  }
  offerBox.className = '';
  offerBox.innerHTML = bits.join('');
  invoiceBtn.disabled = !sess.agreement_quote || !!sess.closed;
  dealStatus.textContent = sess.closed
    ? 'This deal is closed. See the invoice board.'
    : sess.agreement_quote
      ? 'The checker can now review a close. Create the invoice if you want PayPal to issue it.'
      : '';
  if (sess.invoice_pk) selectProofInvoice(sess.invoice_pk);
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
  session = data;
  showUsageNote('');
  buyerInput.disabled = false;
  sendChatBtn.disabled = false;
  invoiceBtn.disabled = true;
  invoiceStatus.textContent = '';
  renderThread(data.messages);
  renderOffer(data);
  buyerInput.focus();
}

document.querySelectorAll('.shop-card').forEach((card) => {
  card.addEventListener('click', () => startShop(card.dataset.shop));
});

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!session) return;
  const text = buyerInput.value.trim();
  if (!text) return;
  buyerInput.value = '';
  sendChatBtn.disabled = true;
  try {
    const res = await fetch('/api/chats/' + session.id + '/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) {
      dealStatus.textContent = data.detail || 'The message could not be sent.';
      return;
    }
    showUsageNote(data.usage_note);
    renderThread(data.session.messages);
    renderOffer(data.session);
  } finally {
    sendChatBtn.disabled = false;
    buyerInput.focus();
  }
});

invoiceBtn.addEventListener('click', async () => {
  if (!session) return;
  invoiceBtn.disabled = true;
  invoiceStatus.textContent = 'Creating invoice…';
  try {
    const res = await fetch('/api/chats/' + session.id + '/invoice', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      invoiceStatus.textContent = 'Invoice sent. Open the pay link from the board.';
      renderOffer(data.session);
      await loadInvoices();
    } else {
      invoiceStatus.textContent = data.reason || data.error || 'The checker blocked this invoice.';
      if (data.session) renderOffer(data.session);
    }
  } finally {
    invoiceBtn.disabled = !session || !session.agreement_quote || (session && session.closed);
  }
});

function selectProofInvoice(id) {
  activeInvoiceId = id;
  proofPanel.classList.remove('hidden');
  proofResult.innerHTML = '<p class="hint">Checking proofs against invoice #' + escapeHtml(String(id)) + '.</p>';
}

proofBtn.addEventListener('click', async () => {
  if (!activeInvoiceId) {
    proofResult.innerHTML = '<p class="hint">Create or select an invoice first.</p>';
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
      res = await fetch('/api/invoices/' + activeInvoiceId + '/proof', { method: 'POST', body });
    } else {
      res = await fetch('/api/invoices/' + activeInvoiceId + '/proof', {
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
      '<p class="hint">This result does not mark the board paid by itself.</p>' + usage + '</div>';
  } finally {
    proofBtn.disabled = false;
  }
});

briefBtn.addEventListener('click', async () => {
  const res = await fetch('/api/briefing');
  const data = await res.json();
  briefingSpeech = (data.speech && data.speech.text) || data.text || '';
  briefText.textContent = briefingSpeech;
  speakBtn.disabled = !briefingSpeech;
  if (data.usage_note) showUsageNote(data.usage_note);
});

speakBtn.addEventListener('click', () => {
  if (!briefingSpeech) return;
  if (!window.speechSynthesis) {
    briefText.textContent = briefingSpeech + ' (This browser has no speech engine; the written briefing is the fallback.)';
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(briefingSpeech);
  utterance.lang = 'en-US';
  window.speechSynthesis.speak(utterance);
});

bindSampleButtons();
