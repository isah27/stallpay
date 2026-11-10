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
const openLoader = document.getElementById('open-loader');

let session = null;
let sendChain = Promise.resolve();

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function prewarmShop() {
  if (!openLoader) return;
  const alreadyReady = sessionStorage.getItem('stallpay-ready') === '1';
  let shown = false;
  const show = () => {
    if (!shown && sessionStorage.getItem('stallpay-ready') !== '1') {
      shown = true;
      openLoader.classList.remove('hidden');
    }
  };
  if (!alreadyReady) {
    setTimeout(show, 300);
  }
  const hide = () => {
    sessionStorage.setItem('stallpay-ready', '1');
    openLoader.classList.add('hidden');
  };
  fetch('/health')
    .then(hide)
    .catch(() => {
      show();
      return fetch('/health').then(hide).catch(hide);
    });
}

function showShops() {
  session = null;
  viewShops.classList.remove('hidden');
  viewChat.classList.add('hidden');
  payCard.classList.add('hidden');
  dealStatus.textContent = '';
  document.querySelectorAll('.shop-card').forEach((card) => card.classList.remove('active'));
}

function appendBubble(role, text) {
  const div = document.createElement('div');
  div.className = 'bubble ' + role;
  const who = role === 'seller' ? 'Shop' : 'You';
  div.innerHTML = '<span class="who">' + who + '</span>' + escapeHtml(text);
  threadEl.appendChild(div);
  threadEl.scrollTop = threadEl.scrollHeight;
  return div;
}

function showTyping() {
  hideTyping();
  const div = document.createElement('div');
  div.className = 'bubble seller typing';
  div.id = 'typing-indicator';
  div.innerHTML = '<span class="who">Shop</span><span class="dots" aria-label="typing"><i></i><i></i><i></i></span>';
  threadEl.appendChild(div);
  threadEl.scrollTop = threadEl.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function renderThread(messages) {
  threadEl.innerHTML = (messages || [])
    .map((m) => {
      const who = m.role === 'seller' ? 'Shop' : 'You';
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
  const status = (sess.invoice_status || '').toLowerCase();
  if (status === 'paid') {
    payStatus.textContent = 'Payment received.';
  } else if (status) {
    payStatus.textContent = 'Waiting for payment.';
  } else {
    payStatus.textContent = '';
  }
}

function renderSession(sess) {
  session = sess;
  if (!sess) return;
  const shop = sess.shop;
  shopTitle.textContent = shop.name;
  shopSub.textContent = shop.city + (shop.seller_name ? ' · ' + shop.seller_name : '');
  renderThread(sess.messages);
  renderChips(shop, (sess.items || []).map((item) => item.id));
  dealStatus.textContent = '';
  renderPay(sess);
}

async function startShop(shopId) {
  const card = document.querySelector('.shop-card[data-shop="' + shopId + '"]');
  document.querySelectorAll('.shop-card').forEach((el) => {
    el.classList.toggle('active', el.dataset.shop === shopId);
  });
  viewShops.classList.add('hidden');
  viewChat.classList.remove('hidden');
  payCard.classList.add('hidden');
  proofResult.innerHTML = '';
  dealStatus.textContent = '';
  if (card) {
    shopTitle.textContent = (card.querySelector('strong') || {}).textContent || 'Shop';
    const loc = (card.querySelector('span') || {}).textContent || '';
    const who = (card.querySelector('em') || {}).textContent || '';
    shopSub.textContent = [loc, who].filter(Boolean).join(' · ');
  }
  threadEl.innerHTML = '';
  itemChips.hidden = true;
  showTyping();
  try {
    const res = await fetch('/api/chats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shop_id: shopId }),
    });
    const data = await res.json();
    hideTyping();
    if (!res.ok) {
      dealStatus.textContent = 'Could not open that shop. Please try again.';
      showShops();
      return;
    }
    renderSession(data);
    buyerInput.focus();
  } catch (err) {
    hideTyping();
    dealStatus.textContent = 'Could not open that shop. Please try again.';
    showShops();
  }
}

function sendBuyer(payload, displayText) {
  if (!session) return sendChain;
  if (displayText) {
    appendBubble('buyer', displayText);
  }
  showTyping();
  const run = async () => {
    try {
      const res = await fetch('/api/chats/' + session.id + '/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      hideTyping();
      if (!res.ok) {
        dealStatus.textContent = 'Your message could not be sent. Please try again.';
        return;
      }
      renderSession(data.session);
      if (data.reason && !data.invoiced && !data.session.pay_url) {
        dealStatus.textContent = 'We could not create the payment link. Please try again.';
      }
    } catch (err) {
      hideTyping();
      dealStatus.textContent = 'Your message could not be sent. Please try again.';
    } finally {
      buyerInput.focus();
    }
  };
  sendChain = sendChain.then(run, run);
  return sendChain;
}

document.querySelectorAll('.shop-card').forEach((card) => {
  card.addEventListener('click', () => startShop(card.dataset.shop));
});

document.getElementById('change-shop-btn').addEventListener('click', showShops);

itemChips.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-item]');
  if (!button || !session) return;
  sendBuyer({ item_id: button.dataset.item }, button.textContent.trim());
});

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = buyerInput.value.trim();
  if (!text || !session) return;
  buyerInput.value = '';
  sendBuyer({ text }, text);
});

refreshBtn.addEventListener('click', async () => {
  if (!session || !session.invoice_pk) return;
  refreshBtn.disabled = true;
  try {
    const res = await fetch('/api/invoices/' + session.invoice_pk + '/refresh', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      payStatus.textContent = 'Could not refresh just now. Please try again.';
      return;
    }
    session.invoice_status = data.status;
    renderPay(session);
  } finally {
    refreshBtn.disabled = false;
  }
});

proofBtn.addEventListener('click', async () => {
  if (!session || !session.invoice_pk) {
    proofResult.innerHTML = '<p class="hint">The pay link appears after you say you want the item. Then you can send a receipt.</p>';
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
      proofResult.innerHTML = '<div class="verdict amount_or_reference_mismatch">' + escapeHtml(data.detail || 'We could not check that receipt.') + '</div>';
      return;
    }
    proofResult.innerHTML =
      '<div class="verdict ' + escapeHtml(data.verdict) + '"><strong>' + escapeHtml(data.summary) + '</strong></div>';
  } finally {
    proofBtn.disabled = false;
  }
});

prewarmShop();
