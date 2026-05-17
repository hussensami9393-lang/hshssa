// ═══════════════════════════════════════════════
//  Stars → TON  |  Frontend JS
//  - Live price fetching (CoinGecko)
//  - Real-time converter
//  - Rate table update
//  - Copy bot link
//  - FAQ accordion
// ═══════════════════════════════════════════════

/* ── Config ──────────────────────────────────── */
const BOT_USERNAME   = 'YourBotUsername'; // ← change this
const STAR_PRICE_USD = 0.013;             // Telegram official
const COMMISSION     = 0.05;             // 5%
const UPDATE_INTERVAL = 60_000;          // ms

/* ── State ───────────────────────────────────── */
let currentTonPrice = 5.00;
let priceChangeDir  = 'neutral';

/* ═══════════════════════════════════════════════
   PRICE FETCHING
═══════════════════════════════════════════════ */
async function fetchTonPrice() {
  try {
    const res = await fetch(
      'https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd',
      { signal: AbortSignal.timeout(8000) }
    );
    if (!res.ok) throw new Error('API error');
    const data = await res.json();
    return parseFloat(data['the-open-network']['usd']);
  } catch {
    // Fallback to OKX
    try {
      const res2 = await fetch(
        'https://www.okx.com/api/v5/market/ticker?instId=TON-USDT',
        { signal: AbortSignal.timeout(8000) }
      );
      const d2 = await res2.json();
      return parseFloat(d2.data[0].last);
    } catch {
      return currentTonPrice; // keep last value
    }
  }
}

async function updatePrice() {
  const newPrice = await fetchTonPrice();
  priceChangeDir = newPrice > currentTonPrice ? 'up'
                 : newPrice < currentTonPrice ? 'down' : 'neutral';
  currentTonPrice = newPrice;

  // Update all price displays
  document.querySelectorAll('[data-ton-price]').forEach(el => {
    el.textContent = `$${newPrice.toFixed(2)}`;
    if (priceChangeDir === 'up')   el.classList.add('price-up');
    if (priceChangeDir === 'down') el.classList.add('price-down');
    setTimeout(() => {
      el.classList.remove('price-up', 'price-down');
    }, 2000);
  });

  // Update stars-per-TON display
  const starsPerTon = Math.ceil(newPrice / STAR_PRICE_USD);
  document.querySelectorAll('[data-stars-per-ton]').forEach(el => {
    el.textContent = starsPerTon.toLocaleString();
  });

  // Refresh converter & table
  recalculate();
  updateRatesTable();

  // Update last-update time
  const now = new Date();
  document.querySelectorAll('[data-last-update]').forEach(el => {
    el.textContent = now.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
  });
}

/* ═══════════════════════════════════════════════
   CONVERTER CALCULATOR
═══════════════════════════════════════════════ */
function calcConversion(stars) {
  const totalUsd      = stars * STAR_PRICE_USD;
  const totalTon      = totalUsd / currentTonPrice;
  const commissionTon = totalTon * COMMISSION;
  const netTon        = totalTon - commissionTon;
  return {
    stars,
    totalUsd:      totalUsd.toFixed(3),
    totalTon:      totalTon.toFixed(6),
    commissionTon: commissionTon.toFixed(6),
    netTon:        netTon.toFixed(6),
    commissionPct: 5
  };
}

function recalculate() {
  const input  = document.getElementById('starsInput');
  const stars  = parseInt(input?.value) || 0;

  if (stars <= 0) {
    setResultPlaceholder();
    return;
  }

  const c = calcConversion(stars);

  // Main result
  const el = document.getElementById('resultTon');
  if (el) el.textContent = `${c.netTon} TON`;

  // Details
  setText('detailUsd',        `$${c.totalUsd}`);
  setText('detailTonTotal',   `${c.totalTon} TON`);
  setText('detailCommission', `${c.commissionTon} TON (5%)`);
  setText('detailNet',        `${c.netTon} TON`);

  // Update bot link
  updateBotLink(stars);
}

function setResultPlaceholder() {
  const el = document.getElementById('resultTon');
  if (el) el.textContent = '0.000000 TON';
  setText('detailUsd',        '$0.000');
  setText('detailTonTotal',   '0 TON');
  setText('detailCommission', '0 TON (5%)');
  setText('detailNet',        '0 TON');
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function updateBotLink(stars) {
  const link = `https://t.me/${BOT_USERNAME}?start=pay_${stars}`;
  const el = document.getElementById('dynamicBotLink');
  if (el) {
    el.href = link;
    el.innerHTML = `
      <span>🤖</span>
      <span>افتح البوت وادفع ${stars.toLocaleString()} ⭐</span>
    `;
  }
  const linkDisplay = document.getElementById('linkPreview');
  if (linkDisplay) linkDisplay.textContent = link;
}

/* ═══════════════════════════════════════════════
   RATES TABLE
═══════════════════════════════════════════════ */
const RATE_AMOUNTS = [50, 100, 250, 500, 1000, 2500, 5000, 10000];
const POPULAR      = [500, 1000];

function updateRatesTable() {
  const tbody = document.getElementById('ratesTableBody');
  if (!tbody) return;

  tbody.innerHTML = RATE_AMOUNTS.map(stars => {
    const c = calcConversion(stars);
    const isPopular = POPULAR.includes(stars);
    return `
      <tr>
        <td class="stars-cell">
          ${isPopular ? `<span class="badge-popular">شائع</span>` : ''}
          ⭐ ${stars.toLocaleString()}
        </td>
        <td class="usd-cell">$${c.totalUsd}</td>
        <td class="ton-cell">💎 ${c.netTon}</td>
        <td>
          <a href="https://t.me/${BOT_USERNAME}?start=pay_${stars}"
             target="_blank"
             class="btn-primary"
             style="padding:7px 16px;font-size:0.78rem;border-radius:50px;display:inline-flex;gap:6px;">
            ⭐ تحويل
          </a>
        </td>
      </tr>
    `;
  }).join('');
}

/* ═══════════════════════════════════════════════
   QUICK AMOUNT BUTTONS
═══════════════════════════════════════════════ */
function selectQuickAmount(amount) {
  const input = document.getElementById('starsInput');
  if (input) {
    input.value = amount;
    recalculate();
  }
  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.classList.toggle('active', parseInt(btn.dataset.amount) === amount);
  });
}

/* ═══════════════════════════════════════════════
   COPY FUNCTIONALITY
═══════════════════════════════════════════════ */
function copyLink() {
  const input   = document.getElementById('starsInput');
  const stars   = parseInt(input?.value) || 100;
  const link    = `https://t.me/${BOT_USERNAME}?start=pay_${stars}`;
  navigator.clipboard.writeText(link).then(() => showToast('✅ تم نسخ الرابط!'));
}

function copyBotLink() {
  const link = `https://t.me/${BOT_USERNAME}`;
  navigator.clipboard.writeText(link).then(() => showToast('✅ تم نسخ رابط البوت!'));
}

/* ═══════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════ */
function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2800);
}

/* ═══════════════════════════════════════════════
   FAQ ACCORDION
═══════════════════════════════════════════════ */
function initFAQ() {
  document.querySelectorAll('.faq-question').forEach(q => {
    q.addEventListener('click', () => {
      const item = q.closest('.faq-item');
      const isOpen = item.classList.contains('open');
      // Close all
      document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
      // Toggle this
      if (!isOpen) item.classList.add('open');
    });
  });
}

/* ═══════════════════════════════════════════════
   FLOATING COINS ANIMATION
═══════════════════════════════════════════════ */
function spawnCoins() {
  const container = document.querySelector('.floating-coins');
  if (!container) return;
  const symbols = ['⭐', '💎', '💰', '🪙', '✨'];
  const count   = window.innerWidth < 600 ? 6 : 14;

  for (let i = 0; i < count; i++) {
    const coin = document.createElement('div');
    coin.className = 'coin';
    coin.textContent = symbols[Math.floor(Math.random() * symbols.length)];
    coin.style.left      = Math.random() * 100 + '%';
    coin.style.animationDuration  = (6 + Math.random() * 10) + 's';
    coin.style.animationDelay     = (Math.random() * 10) + 's';
    coin.style.fontSize  = (1.2 + Math.random() * 1.4) + 'rem';
    container.appendChild(coin);
  }
}

/* ═══════════════════════════════════════════════
   SMOOTH SCROLL FOR NAV LINKS
═══════════════════════════════════════════════ */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

/* ═══════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  // Init animations
  spawnCoins();
  initFAQ();
  initSmoothScroll();

  // Fetch initial price
  await updatePrice();

  // Wire converter input
  const starsInput = document.getElementById('starsInput');
  if (starsInput) {
    starsInput.addEventListener('input', recalculate);
    starsInput.addEventListener('keypress', e => {
      if (!/[0-9]/.test(e.key)) e.preventDefault();
    });
  }

  // Start live price updater
  setInterval(updatePrice, UPDATE_INTERVAL);

  // Set initial quick btn
  selectQuickAmount(100);
});
