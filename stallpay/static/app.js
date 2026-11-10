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

let lastOrder = null;

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
    tr.querySelector('.item-price').value = item.unit_price_ngn || '';
    tr.querySelector('.line-total').textContent = item.line_total_ngn_display || '';
    linesBody.appendChild(tr);
  });
  if (check.ok) {
    conversion.textContent =
      'PayPal will collect ' +
      check.usd_total_display +
      ' at 1 USD = ₦' +
      check.rate +
      ' (dated ' +
      check.rate_as_of +
      '). Original naira total ' +
      check.computed_total_ngn_display +
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
      const remind = ['paid', 'cancelled', 'refunded'].includes(inv.status)
        ? ''
        : '<button type="button" class="remind" data-id="' + inv.id + '">Send reminder</button>';
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
        remind +
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

bindSampleButtons();
