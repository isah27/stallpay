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

const langSelect = document.getElementById('lang-select');
const shopsHeading = document.getElementById('shops-heading');
const changeShopBtn = document.getElementById('change-shop-btn');
const payTitle = document.getElementById('pay-title');
const payLinkLabel = document.getElementById('pay-link-label');
const proofTitle = document.getElementById('proof-title');
const proofHint = document.getElementById('proof-hint');
const sellerToolsLink = document.getElementById('seller-tools-link');
const openLoaderText = document.getElementById('open-loader-text');
const langLabel = document.getElementById('lang-label');

const UI_TEXT = {
  en: {
    langLabel: 'Language',
    shopsHeading: 'Select the shop you want to buy from.',
    changeShop: 'Change shop',
    input: 'Write a message…',
    send: 'Send',
    yourMessage: 'Your message',
    payTitle: 'Pay for this order',
    payLink: 'Pay with PayPal',
    refresh: 'Refresh payment status',
    paid: 'Payment received.',
    waiting: 'Waiting for payment.',
    proofTitle: 'Already paid?',
    proofHint: 'Send a photo or the text of your receipt and we’ll check it.',
    proofPlaceholder: 'Paste your receipt here…',
    proofBtn: 'Check my payment',
    opening: 'Opening the shop…',
    sellerTools: 'Seller tools',
    shop: 'Shop',
    you: 'You',
    openError: 'Could not open that shop. Please try again.',
    sendError: 'Your message could not be sent. Please try again.',
    invoiceError: 'We could not create the payment link. Please try again.',
    refreshError: 'Could not refresh just now. Please try again.',
    proofNeedDeal: 'The pay link appears after you say you want the item. Then you can send a receipt.',
    proofError: 'We could not check that receipt.',
  },
  es: {
    langLabel: 'Idioma',
    shopsHeading: 'Elige la tienda en la que quieres comprar.',
    changeShop: 'Cambiar de tienda',
    input: 'Escribe un mensaje…',
    send: 'Enviar',
    yourMessage: 'Tu mensaje',
    payTitle: 'Paga este pedido',
    payLink: 'Pagar con PayPal',
    refresh: 'Actualizar el estado del pago',
    paid: 'Pago recibido.',
    waiting: 'Esperando el pago.',
    proofTitle: '¿Ya pagaste?',
    proofHint: 'Envía una foto o el texto de tu recibo y lo revisamos.',
    proofPlaceholder: 'Pega tu recibo aquí…',
    proofBtn: 'Revisar mi pago',
    opening: 'Abriendo la tienda…',
    sellerTools: 'Herramientas del vendedor',
    shop: 'Tienda',
    you: 'Tú',
    openError: 'No se pudo abrir esa tienda. Inténtalo de nuevo.',
    sendError: 'No se pudo enviar tu mensaje. Inténtalo de nuevo.',
    invoiceError: 'No se pudo crear el enlace de pago. Inténtalo de nuevo.',
    refreshError: 'No se pudo actualizar ahora. Inténtalo de nuevo.',
    proofNeedDeal: 'El enlace de pago aparece cuando dices que quieres el artículo. Luego puedes enviar un recibo.',
    proofError: 'No pudimos revisar ese recibo.',
  },
  hi: {
    langLabel: 'भाषा',
    shopsHeading: 'Woh shop chunein jahan se aap kharidna chahte hain.',
    changeShop: 'Shop badlein',
    input: 'Apna message likhein…',
    send: 'Bhejein',
    yourMessage: 'Aapka message',
    payTitle: 'Is order ka payment karein',
    payLink: 'PayPal se pay karein',
    refresh: 'Payment status refresh karein',
    paid: 'Payment mil gaya.',
    waiting: 'Payment ka wait ho raha hai.',
    proofTitle: 'Pehle se pay kar diya?',
    proofHint: 'Receipt ki photo ya text bhejein, hum check karenge.',
    proofPlaceholder: 'Apni receipt yahan paste karein…',
    proofBtn: 'Mera payment check karein',
    opening: 'Shop khul rahi hai…',
    sellerTools: 'Seller tools',
    shop: 'Shop',
    you: 'Aap',
    openError: 'Woh shop nahi khul pai. Phir se try karein.',
    sendError: 'Message nahi ja saka. Phir se try karein.',
    invoiceError: 'Payment link nahi ban saka. Phir se try karein.',
    refreshError: 'Abhi refresh nahi ho saka. Phir se try karein.',
    proofNeedDeal: 'Jab aap clearly haan bolenge tab pay link dikhega. Uske baad receipt bhej sakte hain.',
    proofError: 'Is receipt ko check nahi kar paye.',
  },
  pcm: {
    langLabel: 'Language',
    shopsHeading: 'Select the shop wey you wan buy from.',
    changeShop: 'Change shop',
    input: 'Write your message…',
    send: 'Send',
    yourMessage: 'Your message',
    payTitle: 'Pay for this order',
    payLink: 'Pay with PayPal',
    refresh: 'Refresh payment status',
    paid: 'Payment don enter.',
    waiting: 'We dey wait for payment.',
    proofTitle: 'You don pay?',
    proofHint: 'Send photo or the text of your receipt, make we check am.',
    proofPlaceholder: 'Paste your receipt here…',
    proofBtn: 'Check my payment',
    opening: 'Shop dey open…',
    sellerTools: 'Seller tools',
    shop: 'Shop',
    you: 'You',
    openError: 'The shop no open. Abeg try again.',
    sendError: 'Your message no send. Abeg try again.',
    invoiceError: 'We no fit create the payment link. Abeg try again.',
    refreshError: 'E no refresh now. Abeg try again.',
    proofNeedDeal: 'The pay link go show after you talk say you wan the item. Then you fit send receipt.',
    proofError: 'We no fit check that receipt.',
  },
  fr: {
    langLabel: 'Langue',
    shopsHeading: 'Choisissez la boutique où vous souhaitez acheter.',
    changeShop: 'Changer de boutique',
    input: 'Écrivez un message…',
    send: 'Envoyer',
    yourMessage: 'Votre message',
    payTitle: 'Régler cette commande',
    payLink: 'Payer avec PayPal',
    refresh: 'Actualiser le statut du paiement',
    paid: 'Paiement reçu.',
    waiting: 'En attente du paiement.',
    proofTitle: 'Déjà payé ?',
    proofHint: 'Envoyez une photo ou le texte de votre reçu, nous le vérifierons.',
    proofPlaceholder: 'Collez votre reçu ici…',
    proofBtn: 'Vérifier mon paiement',
    opening: 'Ouverture de la boutique…',
    sellerTools: 'Outils vendeur',
    shop: 'Boutique',
    you: 'Vous',
    openError: 'Impossible d’ouvrir cette boutique. Veuillez réessayer.',
    sendError: 'Votre message n’a pas pu être envoyé. Veuillez réessayer.',
    invoiceError: 'Impossible de créer le lien de paiement. Veuillez réessayer.',
    refreshError: 'Actualisation impossible pour le moment. Veuillez réessayer.',
    proofNeedDeal: 'Le lien de paiement apparaît lorsque vous dites clairement que vous voulez l’article. Vous pourrez ensuite envoyer un reçu.',
    proofError: 'Nous n’avons pas pu vérifier ce reçu.',
  },
};

function currentLang() {
  const stored = (sessionStorage.getItem('stallpay-lang') || (langSelect && langSelect.value) || 'en').toLowerCase();
  return UI_TEXT[stored] ? stored : 'en';
}

function t(key) {
  const pack = UI_TEXT[currentLang()] || UI_TEXT.en;
  return pack[key] || UI_TEXT.en[key] || key;
}

function applyUI() {
  const lang = currentLang();
  document.documentElement.lang = lang === 'pcm' ? 'en' : lang;
  if (langSelect && langSelect.value !== lang) langSelect.value = lang;
  if (langLabel) langLabel.textContent = t('langLabel');
  if (shopsHeading) shopsHeading.textContent = t('shopsHeading');
  if (changeShopBtn) changeShopBtn.textContent = t('changeShop');
  if (buyerInput) buyerInput.placeholder = t('input');
  const inputLabel = document.querySelector('label[for="buyer-input"]');
  if (inputLabel) inputLabel.textContent = t('yourMessage');
  if (sendChatBtn) sendChatBtn.textContent = t('send');
  if (payTitle) payTitle.textContent = t('payTitle');
  if (payLinkLabel) payLinkLabel.textContent = t('payLink');
  if (refreshBtn) refreshBtn.textContent = t('refresh');
  if (proofTitle) proofTitle.textContent = t('proofTitle');
  if (proofHint) proofHint.textContent = t('proofHint');
  if (proofText) proofText.placeholder = t('proofPlaceholder');
  if (proofBtn) proofBtn.textContent = t('proofBtn');
  if (openLoaderText) openLoaderText.textContent = t('opening');
  if (sellerToolsLink) sellerToolsLink.textContent = t('sellerTools');
}

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
  const who = role === 'seller' ? t('shop') : t('you');
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
      const who = m.role === 'seller' ? t('shop') : t('you');
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
    payStatus.textContent = t('paid');
  } else if (status) {
    payStatus.textContent = t('waiting');
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
      body: JSON.stringify({ shop_id: shopId, language: currentLang() }),
    });
    const data = await res.json();
    hideTyping();
    if (!res.ok) {
      dealStatus.textContent = t('openError');
      showShops();
      return;
    }
    renderSession(data);
    buyerInput.focus();
  } catch (err) {
    hideTyping();
    dealStatus.textContent = t('openError');
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
        dealStatus.textContent = t('sendError');
        return;
      }
      renderSession(data.session);
      if (data.reason && !data.invoiced && !data.session.pay_url) {
        dealStatus.textContent = t('invoiceError');
      }
    } catch (err) {
      hideTyping();
      dealStatus.textContent = t('sendError');
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
      payStatus.textContent = t('refreshError');
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
    proofResult.innerHTML = '<p class="hint">' + escapeHtml(t('proofNeedDeal')) + '</p>';
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
      proofResult.innerHTML = '<div class="verdict amount_or_reference_mismatch">' + escapeHtml(data.detail || t('proofError')) + '</div>';
      return;
    }
    proofResult.innerHTML =
      '<div class="verdict ' + escapeHtml(data.verdict) + '"><strong>' + escapeHtml(data.summary) + '</strong></div>';
  } finally {
    proofBtn.disabled = false;
  }
});

async function setBuyerLanguage(lang) {
  const chosen = UI_TEXT[lang] ? lang : 'en';
  sessionStorage.setItem('stallpay-lang', chosen);
  applyUI();
  if (!session) return;
  try {
    const res = await fetch('/api/chats/' + session.id + '/language', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: chosen }),
    });
    const data = await res.json();
    if (res.ok) renderSession(data);
  } catch (err) {
    // The next message will still use the selected language once the shop is reopened.
  }
}

if (langSelect) {
  const stored = currentLang();
  langSelect.value = stored;
  applyUI();
  langSelect.addEventListener('change', () => setBuyerLanguage(langSelect.value));
} else {
  applyUI();
}

prewarmShop();
