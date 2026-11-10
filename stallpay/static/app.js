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
const chatUi = document.getElementById('chat-ui');
const orderCard = document.getElementById('order-card');
const payStatus = document.getElementById('pay-status');
const paypalBtn = document.getElementById('paypal-btn');
const alreadyPaidBtn = document.getElementById('already-paid-btn');
const openLoader = document.getElementById('open-loader');

const langSelect = document.getElementById('lang-select');
const shopsHeading = document.getElementById('shops-heading');
const changeShopBtn = document.getElementById('change-shop-btn');
const sellerToolsLink = document.getElementById('seller-tools-link');
const summaryTitle = document.getElementById('summary-title');
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


const UI_SUMMARY = {
  en: {
    summaryTitle: 'Order summary',
    thItem: 'Item',
    thQty: 'Qty',
    thPrice: 'List price',
    labelList: 'List price',
    labelPromo: 'Promo discount',
    labelTotal: 'Total',
    labelUsd: 'Billed in USD',
    labelInvoice: 'Invoice number',
    alreadyPaid: "I've already paid",
    paidConfirm: "PayPal has confirmed this payment. Thank you — you're all set.",
    notPaidYet: "PayPal hasn't confirmed payment yet. You can proceed with PayPal, or check again in a moment.",
    promoUntil: 'Ends {ends}',
    checkError: 'We could not check with PayPal just now. Please try again.',
  },
  es: {
    summaryTitle: 'Resumen del pedido',
    thItem: 'Artículo',
    thQty: 'Cant.',
    thPrice: 'Precio de lista',
    labelList: 'Precio de lista',
    labelPromo: 'Descuento de promo',
    labelTotal: 'Total',
    labelUsd: 'Facturado en USD',
    labelInvoice: 'Número de factura',
    alreadyPaid: 'Ya pagué',
    paidConfirm: 'PayPal confirmó este pago. Gracias, ya está listo.',
    notPaidYet: 'PayPal aún no confirma el pago. Puedes continuar con PayPal, o volver a comprobar en un momento.',
    promoUntil: 'Termina {ends}',
    checkError: 'No pudimos consultar a PayPal ahora. Inténtalo de nuevo.',
  },
  hi: {
    summaryTitle: 'Order summary',
    thItem: 'Item',
    thQty: 'Qty',
    thPrice: 'List price',
    labelList: 'List price',
    labelPromo: 'Promo discount',
    labelTotal: 'Total',
    labelUsd: 'USD mein bill',
    labelInvoice: 'Invoice number',
    alreadyPaid: 'Maine pehle pay kar diya hai',
    paidConfirm: 'PayPal ne is payment ko confirm kar diya hai. Shukriya, ho gaya.',
    notPaidYet: 'PayPal ne abhi payment confirm nahi kiya. PayPal se proceed karein, ya thodi der baad check karein.',
    promoUntil: '{ends} tak',
    checkError: 'PayPal se check nahi ho paya. Phir se try karein.',
  },
  pcm: {
    summaryTitle: 'Order summary',
    thItem: 'Item',
    thQty: 'Qty',
    thPrice: 'List price',
    labelList: 'List price',
    labelPromo: 'Promo discount',
    labelTotal: 'Total',
    labelUsd: 'Dem bill am in USD',
    labelInvoice: 'Invoice number',
    alreadyPaid: 'I don pay already',
    paidConfirm: 'PayPal don confirm this payment. Thank you, e don set.',
    notPaidYet: 'PayPal never confirm the payment. You fit proceed with PayPal, or check again small time.',
    promoUntil: 'E end {ends}',
    checkError: 'We no fit check with PayPal now. Abeg try again.',
  },
  fr: {
    summaryTitle: 'Récapitulatif de la commande',
    thItem: 'Article',
    thQty: 'Qté',
    thPrice: 'Prix affiché',
    labelList: 'Prix affiché',
    labelPromo: 'Remise promo',
    labelTotal: 'Total',
    labelUsd: 'Facturé en USD',
    labelInvoice: 'Numéro de facture',
    alreadyPaid: "J'ai déjà payé",
    paidConfirm: 'PayPal a confirmé ce paiement. Merci, tout est en ordre.',
    notPaidYet: "PayPal n'a pas encore confirmé le paiement. Vous pouvez continuer avec PayPal, ou vérifier à nouveau dans un instant.",
    promoUntil: 'Se termine {ends}',
    checkError: 'Impossible de vérifier auprès de PayPal pour le moment. Veuillez réessayer.',
  },
};

function currentLang() {
  const stored = (sessionStorage.getItem('stallpay-lang') || (langSelect && langSelect.value) || 'en').toLowerCase();
  return UI_TEXT[stored] ? stored : 'en';
}

function t(key) {
  const lang = currentLang();
  const pack = Object.assign({}, UI_TEXT.en, UI_SUMMARY.en, UI_TEXT[lang] || {}, UI_SUMMARY[lang] || {});
  return pack[key] || key;
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
  if (openLoaderText) openLoaderText.textContent = t('opening');
  if (sellerToolsLink) sellerToolsLink.textContent = t('sellerTools');
  if (summaryTitle) summaryTitle.textContent = t('summaryTitle');
  const ids = {
    'th-item': 'thItem',
    'th-qty': 'thQty',
    'th-price': 'thPrice',
    'label-list': 'labelList',
    'label-promo': 'labelPromo',
    'label-total': 'labelTotal',
    'label-usd': 'labelUsd',
    'label-invoice': 'labelInvoice',
  };
  Object.keys(ids).forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.textContent = t(ids[id]);
  });
  if (alreadyPaidBtn && !orderCard.classList.contains('paid-confirmed')) {
    alreadyPaidBtn.textContent = t('alreadyPaid');
  }
  if (session && session.pay_url) renderPay(session);
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
  hideOrderCard();
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

function hideOrderCard() {
  if (chatUi) chatUi.classList.remove('hidden');
  if (orderCard) {
    orderCard.classList.add('hidden');
    orderCard.classList.remove('paid-confirmed');
  }
  if (payStatus) {
    payStatus.textContent = '';
    payStatus.className = 'pay-status';
  }
}

function renderPay(sess) {
  if (!sess || !sess.pay_url || !sess.order_summary) {
    hideOrderCard();
    return;
  }
  if (chatUi) chatUi.classList.add('hidden');
  orderCard.classList.remove('hidden');
  const summary = sess.order_summary;
  const shopLine = [summary.shop_name, summary.city, summary.country].filter(Boolean).join(' · ');
  document.getElementById('summary-shop').textContent = shopLine;
  const lines = document.getElementById('summary-lines');
  lines.innerHTML = (summary.items || [])
    .map((item) => {
      return (
        '<tr><td>' + escapeHtml(item.name) + '</td><td>' +
        escapeHtml(item.quantity) + '</td><td>' +
        escapeHtml(item.list_price_display) + '</td></tr>'
      );
    })
    .join('');
  document.getElementById('summary-list').textContent = summary.list_total_display || '';
  const promoRow = document.getElementById('summary-promo-row');
  if (summary.promo_discount_display) {
    promoRow.classList.remove('hidden');
    let promo = '−' + summary.promo_discount_display;
    if (summary.promo_ends_display) {
      promo += '<span class="promo-end">' + escapeHtml(t('promoUntil').replace('{ends}', summary.promo_ends_display)) + '</span>';
    }
    document.getElementById('summary-promo').innerHTML = promo;
  } else {
    promoRow.classList.add('hidden');
    document.getElementById('summary-promo').textContent = '';
  }
  document.getElementById('summary-total').textContent = summary.total_display || '';
  const usd = summary.usd_total_display || '';
  document.getElementById('summary-usd').textContent = usd ? usd + ' USD' : '';
  document.getElementById('summary-invoice').textContent = summary.invoice_number || sess.invoice_number || '';
  paypalBtn.href = sess.pay_url;
  paypalBtn.textContent = 'Proceed with PayPal';
  alreadyPaidBtn.textContent = t('alreadyPaid');
  const status = (sess.invoice_status || '').toLowerCase();
  if (status === 'paid') {
    showPaidConfirmation();
  } else if (!payStatus.dataset.locked) {
    payStatus.textContent = '';
    payStatus.className = 'pay-status';
    orderCard.classList.remove('paid-confirmed');
  }
}

function showPaidConfirmation() {
  orderCard.classList.add('paid-confirmed');
  payStatus.textContent = t('paidConfirm');
  payStatus.className = 'pay-status paid';
  payStatus.dataset.locked = '1';
}

function renderSession(sess) {
  session = sess;
  if (!sess) return;
  const shop = sess.shop;
  shopTitle.textContent = shop.name;
  shopSub.textContent = shop.city + (shop.seller_name ? ' · ' + shop.seller_name : '');
  if (!(sess.pay_url && sess.order_summary)) {
    renderThread(sess.messages);
    renderChips(shop, (sess.items || []).map((item) => item.id));
  }
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
  hideOrderCard();
  if (payStatus) delete payStatus.dataset.locked;
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
      if (buyerInput && chatUi && !chatUi.classList.contains('hidden')) buyerInput.focus();
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

alreadyPaidBtn.addEventListener('click', async () => {
  if (!session || !session.invoice_pk) return;
  alreadyPaidBtn.disabled = true;
  try {
    const res = await fetch('/api/invoices/' + session.invoice_pk + '/already-paid', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      payStatus.textContent = t('checkError');
      payStatus.className = 'pay-status unpaid';
      return;
    }
    session.invoice_status = data.status;
    if (data.paid) {
      showPaidConfirmation();
    } else {
      orderCard.classList.remove('paid-confirmed');
      payStatus.textContent = t('notPaidYet');
      payStatus.className = 'pay-status unpaid';
      delete payStatus.dataset.locked;
    }
  } catch (err) {
    payStatus.textContent = t('checkError');
    payStatus.className = 'pay-status unpaid';
  } finally {
    alreadyPaidBtn.disabled = false;
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
