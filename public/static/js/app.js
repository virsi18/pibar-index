/**
 * PiBarX - Global Pi Barter Real-Price Index
 * Obsidian Parity Terminal Client Controller (Stitch AI Generated Architecture)
 */

let allBarters = [];
let allCommodities = [];
let allCountries = [];
let currentFeedMode = "barters";
let latestPiLedger = null;
let currentPioneer = null;
let activeRegionFilter = "ALL";

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[char]);
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("[PiBarX] Obsidian Parity Terminal Engine Initialized.");

  initSidebarAndTabs();
  initCalculator();
  initSubmitModal();
  initSearch();
  initPiIntegration();
  loadAllData();

  // Periodically refresh telemetry
  setInterval(loadSummary, 30000);
});

// ==========================================
// SCROLL & NAVIGATION
// ==========================================

function scrollToSection(sectionId) {
  const elem = document.getElementById(sectionId);
  if (elem) {
    elem.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Update active sidebar nav
  document.querySelectorAll(".nav-link-item").forEach(item => {
    item.classList.remove("active");
  });
  const navMatch = document.querySelector(`.nav-link-item[onclick*="${sectionId}"]`);
  if (navMatch) navMatch.classList.add("active");

  // Dismiss mobile drawer if open
  if (window.innerWidth <= 768) {
    const sidebar = document.getElementById("sidebar-drawer") || document.querySelector(".sidebar");
    const backdrop = document.getElementById("sidebar-backdrop");
    if (sidebar) sidebar.classList.remove("mobile-open");
    if (backdrop) backdrop.classList.remove("mobile-open");
    document.body.style.overflow = "";
  }
}

function initSidebarAndTabs() {
  // Mobile Burger Bar & Drawer Logic
  const burgerBtn = document.getElementById("btn-burger-menu");
  const sidebar = document.getElementById("sidebar-drawer") || document.querySelector(".sidebar");
  const closeBtn = document.getElementById("btn-close-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");

  function openSidebar() {
    if (sidebar) sidebar.classList.add("mobile-open");
    if (backdrop) backdrop.classList.add("mobile-open");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove("mobile-open");
    if (backdrop) backdrop.classList.remove("mobile-open");
    document.body.style.overflow = "";
  }

  if (burgerBtn) burgerBtn.addEventListener("click", openSidebar);
  if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  // Auto-close drawer on mobile when any navigation item is clicked
  document.querySelectorAll(".nav-link-item, .btn-sidebar-submit").forEach(el => {
    el.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        closeSidebar();
      }
    });
  });

  document.querySelectorAll(".header-tab-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.querySelectorAll(".header-tab-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
    });
  });
}

function initSearch() {
  const searchInput = document.getElementById("global-search-input");
  if (searchInput) {
    let debounce = null;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        const q = e.target.value.toLowerCase().trim();
        filterFeedByQuery(q);
      }, 250);
    });
  }
}

function filterFeedByQuery(q) {
  if (currentFeedMode !== "barters") return;
  if (!q) {
    renderBarterTable(allBarters);
    return;
  }
  const filtered = allBarters.filter(b => 
    (b.item_name && b.item_name.toLowerCase().includes(q)) ||
    (b.merchant_name && b.merchant_name.toLowerCase().includes(q)) ||
    (b.city && b.city.toLowerCase().includes(q)) ||
    (b.country_code && b.country_code.toLowerCase().includes(q)) ||
    (b.tx_hash && b.tx_hash.toLowerCase().includes(q))
  );
  renderBarterTable(filtered);
}

// ==========================================
// DATA FETCHING & RENDERING
// ==========================================

async function loadAllData() {
  await Promise.all([
    loadSummary(),
    loadCommodities(),
    loadCountries(),
    loadBarters()
  ]);
}

async function loadSummary() {
  try {
    const res = await fetch("/api/summary");
    if (!res.ok) return;
    const data = await res.json();

    const priceEl = document.getElementById("kpi-price");
    const deltaEl = document.getElementById("kpi-delta-24h");
    const volPiEl = document.getElementById("kpi-vol-pi");
    const volUsdEl = document.getElementById("kpi-vol-usd");
    const tradesEl = document.getElementById("kpi-trades-count");
    const hubsEl = document.getElementById("kpi-hubs");
    if (priceEl) priceEl.textContent = data.global_median_pi_usd == null ? "No verified data" : `1 π = $${Number(data.global_median_pi_usd).toFixed(4)}`;
    if (deltaEl) deltaEl.textContent = data.change_24h_pct == null ? "— 24h" : `${Number(data.change_24h_pct).toFixed(2)}% 24h`;
    if (volPiEl) volPiEl.textContent = `${Number(data.total_volume_24h_pi || 0).toLocaleString()} π`;
    if (volUsdEl) volUsdEl.textContent = `≈ $${Number(data.total_volume_24h_usd || 0).toLocaleString()} USD`;
    if (tradesEl) tradesEl.textContent = Number(data.total_barters_count || 0).toLocaleString();
    if (hubsEl) hubsEl.textContent = `${Number(data.active_countries_count || 0)} active countries`;
    if (data.last_block_sync && document.getElementById("header-block-sync")) document.getElementById("header-block-sync").textContent = data.last_block_sync;
  } catch (err) {
    console.warn("[PiBarX] Summary error:", err);
  }
}

async function loadCommodities() {
  try {
    const res = await fetch("/api/commodities");
    if (!res.ok) return;
    allCommodities = await res.json();
    populateFormCommodities(allCommodities);
    renderCommodities(allCommodities);
  } catch (err) {
    console.warn("[PiBarX] Commodity error:", err);
  }
}

function renderCommodities(commodities) {
  const container = document.getElementById("commodity-cards-container");
  if (!container || !commodities) return;

  container.innerHTML = commodities.slice(0, 5).map(c => {
    const trades = `${Number(c.sample_trades_count || 0)} verified trades`;
    const deltaVal = c.change_24h_pct;
    const deltaClass = deltaVal == null ? "" : (deltaVal >= 0 ? "up" : "down");
    const deltaText = deltaVal == null ? "No trend data" : `${deltaVal >= 0 ? "+" : ""}${Number(deltaVal).toFixed(2)}%`;
    const piPrice = c.median_pi_price == null ? "—" : Number(c.median_pi_price).toFixed(4);
    const benchmark = Number(c.benchmark_usd || 0).toFixed(2);

    return `
      <div class="comm-card" onclick="selectCommodityForCalc('${c.id}')" title="Click to calculate ${c.name}">
        <div class="comm-top-row">
          <span class="comm-tag">${c.icon || "📦"} ${c.symbol || c.id.toUpperCase()}</span>
          <span class="comm-trades">${trades}</span>
        </div>
        <div class="comm-name-row">${c.name}</div>
        <div class="comm-price-row">
          <span class="comm-price-pi">${piPrice === "—" ? "No Pi sample" : `Median paid: ${piPrice} π`}</span>
          <span class="comm-delta ${deltaClass}">${deltaText} 7d</span>
        </div>
        <div class="comm-fiat-eq">Reference ≈ $${benchmark} USD (${c.unit || 'Unit'})</div>
        <div class="comm-spread">Reference basket value only — not a live Pi quote</div>
      </div>
    `;
  }).join("");
}

async function loadCountries() {
  try {
    const res = await fetch("/api/countries");
    if (!res.ok) return;
    allCountries = await res.json();
    populateFormCountries(allCountries);
    renderCountryMatrix(allCountries);
  } catch (err) {
    console.warn("[PiBarX] Countries error:", err);
  }
}

function renderCountryMatrix(countries) {
  const tbody = document.getElementById("country-matrix-body");
  if (!tbody || !countries) return;

  tbody.innerHTML = countries.map(c => {
    const medianUsd = c.median_barter_pi_usd == null ? "—" : Number(c.median_barter_pi_usd).toFixed(4);
    const totalTrades = Number(c.total_barters || 0);
    
    return `
      <tr>
        <td>
          <div style="font-weight: 600; color: #fff; display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 15px;">${c.flag || "🌐"}</span>
            <span>${c.country_name}</span>
            <span style="font-size: 10px; color: var(--text-muted); font-family: var(--font-mono);">${c.currency_code}</span>
          </div>
        </td>
        <td class="font-mono">
          <span style="color: #fff; font-weight: 600;">${medianUsd === "—" ? "No verified rate" : `$${medianUsd} / π`}</span>
          <div style="font-size: 10px; color: var(--text-dim);">${c.currency_code} · configured reference FX</div>
        </td>
        <td class="font-mono" style="color: var(--basket-amber-light);">
          ${c.purchasing_power_ratio == null ? "PPP unavailable" : `PPP ratio: ${Number(c.purchasing_power_ratio).toFixed(3)}`}
        </td>
        <td>
          <span style="background: var(--surface-input); border: 1px solid var(--border-subtle); padding: 2px 6px; border-radius: 4px; font-size: 10px; color: var(--text-dim);">
            ${c.most_popular_commodity || "No sample"}
          </span>
        </td>
        <td class="font-mono" style="color: var(--pi-purple-light); font-weight: 600;">
          ${totalTrades.toLocaleString()} trades
        </td>
        <td class="font-mono" style="color: var(--yield-emerald-light);">${totalTrades ? "Verified" : "Unrated"}</td>
        <td>
          <div class="score-bar-wrap">
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="width: 0%;"></div>
            </div>
            <span class="score-val">${totalTrades ? "Sample available" : "No sample"}</span>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

window.filterMatrixRegion = function(regionCode) {
  document.querySelectorAll("#section-regional .header-tab-pill").forEach(p => p.classList.remove("active"));
  event.target.classList.add("active");

  if (regionCode === "ALL") {
    renderCountryMatrix(allCountries);
    return;
  }

  const regionMapping = {
    "SEA": ["ID", "VN", "PH", "MY"],
    "EA": ["KR", "CN"],
    "AF": ["NG"],
    "AM": ["US"]
  };

  const allowed = regionMapping[regionCode] || [];
  const filtered = allCountries.filter(c => allowed.includes(c.country_code));
  renderCountryMatrix(filtered);
};

// ==========================================
// FEED SWITCHING (AUDITED vs LIVE MAINNET)
// ==========================================

async function loadBarters() {
  try {
    const res = await fetch("/api/barters?limit=28");
    if (!res.ok) return;
    allBarters = await res.json();
    const countTab = document.getElementById("tab-btn-barters");
    if (countTab) countTab.textContent = `🛒 Verified Barters (${allBarters.length})`;
    if (currentFeedMode === "barters") {
      renderBarterTable(allBarters);
    }
  } catch (err) {
    console.warn("[PiBarX] Barters error:", err);
  }
}

function renderBarterTable(barters) {
  const tbody = document.getElementById("feed-table-body");
  if (!tbody) return;

  if (barters.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px; color: var(--text-muted);">No records found matching query.</td></tr>`;
    return;
  }

  tbody.innerHTML = barters.map(b => {
    const txShort = b.tx_hash && b.tx_hash.length === 64
      ? `${b.tx_hash.substring(0, 6)}...${b.tx_hash.substring(58)}`
      : "Missing TxID";

    const txLink = b.tx_hash && b.tx_hash.length === 64
      ? `https://api.mainnet.minepi.com/transactions/${b.tx_hash}`
      : `#`;

    const fiatUsd = Number(b.fiat_usd || 0).toFixed(2);
    const fiatVal = Number(b.fiat_value || 0).toLocaleString();

    return `
      <tr>
        <td class="font-mono">
          <a href="${txLink}" target="_blank" rel="noopener noreferrer" style="color: var(--pi-purple-light); text-decoration: none; font-size: 11px;">
            ${txShort} ↗
          </a>
          <div style="font-size: 9px; color: var(--text-muted);">${(b.timestamp || "").substring(5, 16)}</div>
        </td>
        <td>
          <div style="font-weight: 600; color: #fff; font-size: 11px;">${escapeHtml(b.merchant_name)}</div>
          <div style="font-size: 10px; color: var(--text-dim);">${escapeHtml(b.city)}, ${escapeHtml(b.country_code)}</div>
        </td>
        <td>
          <div style="font-size: 11px; color: #fff;">${escapeHtml(b.item_name)}</div>
          <div style="font-size: 9px; color: var(--text-muted); text-transform: uppercase;">${escapeHtml(b.commodity_id)}</div>
        </td>
        <td class="font-mono" style="font-weight: 700; color: var(--pi-purple-light); font-size: 13px;">
          ${b.pi_amount} π
        </td>
        <td class="font-mono" style="font-size: 11px;">
          $${fiatUsd}
          <div style="font-size: 9px; color: var(--text-muted);">${escapeHtml(b.fiat_currency)} ${fiatVal}</div>
        </td>
        <td>
          <a href="${txLink}" target="_blank" rel="noopener noreferrer" class="btn-invoice-proof" title="Verified Proof Receipt">
            <span>●</span> VERIFIED ON-CHAIN
          </a>
        </td>
      </tr>
    `;
  }).join("");
}

window.switchFeedMode = async function(mode) {
  const btnBarters = document.getElementById("tab-btn-barters");
  const btnOnchain = document.getElementById("tab-btn-onchain");
  const thead = document.getElementById("feed-table-head");
  const tbody = document.getElementById("feed-table-body");

  if (mode === "barters") {
    currentFeedMode = "barters";
    btnBarters.classList.add("active");
    btnOnchain.classList.remove("active");

    thead.innerHTML = `
      <tr>
        <th>Tx Hash & Time</th>
        <th>Pioneer Merchant</th>
        <th>Commodity / Asset</th>
        <th>Settlement (π)</th>
        <th>Fiat Implied</th>
        <th>Invoice Proof</th>
      </tr>
    `;
    renderBarterTable(allBarters);
  } else {
    currentFeedMode = "onchain";
    btnOnchain.classList.add("active");
    btnBarters.classList.remove("active");

    thead.innerHTML = `
      <tr>
        <th>Time (UTC)</th>
        <th>Sender (From)</th>
        <th>Recipient (To)</th>
        <th>Asset Type</th>
        <th>Pi Amount</th>
        <th>On-Chain Status</th>
      </tr>
    `;

    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 24px; color: var(--pi-purple-light);"><span class="pulse-dot" style="display:inline-block; margin-right:6px;"></span>Streaming live blocks from Pi Mainnet Horizon...</td></tr>`;

    try {
      const res = await fetch("/api/pi/live-transactions?limit=25");
      const txs = await res.json();

      if (!txs || txs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px; color: var(--text-dim);">No transactions received from Horizon node.</td></tr>`;
        return;
      }

      tbody.innerHTML = txs.map(t => {
        const timeStr = t.created_at ? t.created_at.replace("T", " ").replace("Z", "") : "Now";
        const fromShort = t.from_address ? `${t.from_address.substring(0, 8)}...${t.from_address.substring(t.from_address.length - 6)}` : "Unknown";
        const toShort = t.to_address ? `${t.to_address.substring(0, 8)}...${t.to_address.substring(t.to_address.length - 6)}` : "Unknown";
        const validTxHash = /^[a-f0-9]{64}$/i.test(t.tx_hash || "");
        const txShort = validTxHash ? `${t.tx_hash.substring(0, 8)}...${t.tx_hash.substring(56)}` : "Tx";
        const txHref = validTxHash ? `https://api.mainnet.minepi.com/transactions/${t.tx_hash}` : "#";

        return `
          <tr>
            <td class="font-mono" style="font-size: 10px; color: var(--text-muted);">${escapeHtml(timeStr)}</td>
            <td>
              <div class="font-mono" style="font-size: 11px; color: #fff;" title="${escapeHtml(t.from_address)}">${escapeHtml(fromShort)}</div>
            </td>
            <td>
              <div class="font-mono" style="font-size: 11px; color: var(--text-dim);" title="${escapeHtml(t.to_address)}">${escapeHtml(toShort)}</div>
            </td>
            <td>
              <span style="font-size: 9px; font-weight: 700; color: #a5b4fc; background: rgba(99,102,241,0.2); padding: 2px 5px; border-radius: 3px;">PI NATIVE</span>
            </td>
            <td class="font-mono" style="font-weight: 700; color: var(--pi-purple-light); font-size: 13px;">
              ${Number(t.amount_pi || 0).toFixed(7)} π
            </td>
            <td>
              <a href="${txHref}" target="_blank" rel="noopener noreferrer" class="btn-invoice-proof" style="color: var(--yield-emerald-light);">
                <span>●</span> ${escapeHtml(txShort)} ↗
              </a>
            </td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 20px; color: var(--danger-crimson);">Error fetching live stream: ${err.message}</td></tr>`;
    }
  }
};

// ==========================================
// CALCULATOR & ARBITRAGE
// ==========================================

function initCalculator() {
  const inputVal = document.getElementById("calc-input-val");
  const currSelect = document.getElementById("calc-currency-select");

  if (inputVal) inputVal.addEventListener("input", runCalculator);
  if (currSelect) currSelect.addEventListener("change", runCalculator);

  runCalculator();
}

async function runCalculator() {
  const inputVal = document.getElementById("calc-input-val");
  const currSelect = document.getElementById("calc-currency-select");
  const resPi = document.getElementById("calc-res-pi");
  const resCorridor = document.getElementById("calc-res-corridor");

  const val = parseFloat(inputVal ? inputVal.value : 100) || 100;
  const curr = currSelect ? currSelect.value : "USD";

  try {
    const res = await fetch(`/api/calculator?fiat_amount=${encodeURIComponent(val)}&fiat_currency=${encodeURIComponent(curr)}`);
    const data = await res.json();

    if (data && data.available === false) {
      if (resPi) resPi.textContent = "Awaiting verified data";
      if (resCorridor) resCorridor.textContent = data.reason || "Calculator unavailable until verified barter data exists.";
      return;
    }
    if (data && data.recommended_pi_range) {
      const fairPi = data.recommended_pi_range.median_fair_pi;
      const consPi = data.recommended_pi_range.conservative_pi;
      const optPi = data.recommended_pi_range.optimistic_pi;

      if (resPi) resPi.textContent = `${fairPi} π`;
      if (resCorridor) resCorridor.textContent = `Indicative ±10% band: ${optPi} π - ${consPi} π (sample median: $${data.implied_rate_usd}/π)`;
    }
  } catch (err) {
    console.warn("[PiBarX] Calc error:", err);
  }
}

window.quickFillCalc = function(amount, curr) {
  const inputVal = document.getElementById("calc-input-val");
  const currSelect = document.getElementById("calc-currency-select");
  if (inputVal) inputVal.value = amount;
  if (currSelect) currSelect.value = curr;
  runCalculator();
};

window.setCalcMode = function(mode) {
  document.getElementById("btn-calc-fiat").classList.toggle("active", mode === "fiat");
  document.getElementById("btn-calc-comm").classList.toggle("active", mode === "comm");
  if (mode === "comm") {
    alert("Commodity-to-Pi mode active: Select any commodity card above to populate standard benchmark values.");
  }
};

function selectCommodityForCalc(commId) {
  const c = allCommodities.find(item => item.id === commId);
  if (c) {
    quickFillCalc(c.benchmark_usd, "USD");
    scrollToSection("section-calculator");
  }
}

// ==========================================
// PI NETWORK INTEGRATION & NODE TELEMETRY
// ==========================================

async function initPiIntegration() {
  await syncPiNetworkTelemetry();
  setInterval(syncPiNetworkTelemetry, 15000);

  const authBtn = document.getElementById("pi-auth-btn");
  const authText = document.getElementById("pi-auth-text");

  // Check Pi Browser
  if (typeof window.Pi !== "undefined") {
    try {
      window.Pi.init({ version: "2.0", sandbox: false });
    } catch (e) {
      console.warn("Pi.init:", e);
    }
  }

  if (authBtn) {
    authBtn.addEventListener("click", async () => {
      if (typeof window.Pi !== "undefined" && window.Pi.authenticate) {
        authText.textContent = "Connecting...";
        try {
          const auth = await window.Pi.authenticate(["username", "payments", "wallet_address"], () => {});
          if (auth && auth.user) {
            currentPioneer = auth.user.username;
            authText.textContent = `@${currentPioneer}`;
            alert(`Pioneer @${currentPioneer} connected successfully via Pi Browser!`);
          }
        } catch (e) {
          authText.textContent = "Connect Node";
          alert("Pi Browser authentication cancelled.");
        }
      } else {
        checkPiNodeDetails();
      }
    });
  }
}

async function syncPiNetworkTelemetry() {
  try {
    const res = await fetch("/api/pi/status");
    if (!res.ok) return;
    const data = await res.json();
    if (data.connected && data.latest_ledger) {
      latestPiLedger = data.latest_ledger;
      const el = document.getElementById("header-block-sync");
      if (el) el.textContent = `Block #${data.latest_ledger.toLocaleString()}`;
    }
  } catch (e) {}
}

window.checkPiNodeDetails = async function() {
  try {
    const response = await fetch("/api/pi/status");
    const data = await response.json();
    const msg = `PI NETWORK MAINNET NODE STATUS\n\n` +
      `• Network: ${data.network || "Pi Network Mainnet"}\n` +
      `• Horizon: ${data.connected ? "Connected" : "Unavailable"}\n` +
      `• Core version: ${data.core_version || "Not reported"}\n` +
      `• Latest ledger: ${data.latest_ledger ? `#${Number(data.latest_ledger).toLocaleString()}` : "Not available"}\n` +
      `• Endpoint: https://api.mainnet.minepi.com\n\n` +
      `${data.connected ? "Live Horizon response received." : "Could not confirm node connectivity."}`;
    alert(msg);
  } catch (error) {
    alert("Pi Horizon status unavailable. Please try again later.");
  }
};

// ==========================================
// BARTER SUBMISSION MODAL
// ==========================================

function initSubmitModal() {
  const modal = document.getElementById("submit-modal");
  const btnOpen = document.getElementById("btn-open-modal");
  const btnClose = document.getElementById("btn-close-modal");
  const form = document.getElementById("submit-barter-form");

  if (btnOpen && modal) {
    btnOpen.addEventListener("click", () => modal.classList.add("active"));
  }
  if (btnClose && modal) {
    btnClose.addEventListener("click", () => modal.classList.remove("active"));
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const statusEl = document.getElementById("form-status-msg");
      statusEl.textContent = "Auditing transaction against Pi Mainnet Horizon...";
      statusEl.style.color = "var(--pi-purple-light)";

      const payload = {
        item_name: document.getElementById("form-item-name").value,
        commodity_id: document.getElementById("form-commodity-id").value,
        country_code: document.getElementById("form-country-code").value,
        city: document.getElementById("form-city").value,
        merchant_name: document.getElementById("form-merchant-name").value,
        pi_amount: parseFloat(document.getElementById("form-pi-amount").value),
        fiat_value: parseFloat(document.getElementById("form-fiat-value").value),
        fiat_currency: "USD",
        tx_hash: document.getElementById("form-tx-hash").value.trim(),
        recipient_address: document.getElementById("form-recipient-address").value.trim().toUpperCase(),
        notes: document.getElementById("form-notes").value
      };

      try {
        const res = await fetch("/api/barters/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const resp = await res.json();

        if (resp.success) {
          statusEl.textContent = "✔ Barter verified & indexed into PiBarX!";
          statusEl.style.color = "var(--yield-emerald-light)";
          setTimeout(() => {
            modal.classList.remove("active");
            form.reset();
            statusEl.textContent = "";
            loadAllData();
          }, 1200);
        } else {
          const detail = resp.detail;
          statusEl.textContent = (typeof detail === "string" ? detail : (detail && detail.message)) || resp.message || "Submission rejected. Check TxID and Pi payment amount.";
          statusEl.style.color = "var(--danger-crimson)";
        }
      } catch (err) {
        statusEl.textContent = "Submission error: " + err.message;
        statusEl.style.color = "var(--danger-crimson)";
      }
    });
  }
}

function populateFormCommodities(commodities) {
  const sel = document.getElementById("form-commodity-id");
  if (!sel) return;
  if (commodities && commodities.length > 0) {
    sel.innerHTML = commodities.map(c => `<option value="${c.id}">${c.icon || "📦"} ${c.name} (${c.symbol || c.id.toUpperCase()})</option>`).join("");
  }
}

function populateFormCountries(countries) {
  const sel = document.getElementById("form-country-code");
  if (!sel) return;
  if (countries && countries.length > 0) {
    sel.innerHTML = countries.map(c => `<option value="${c.country_code}">${c.flag || "🌐"} ${c.country_name} (${c.currency_code})</option>`).join("");
  }
}
