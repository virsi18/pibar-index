/**
 * PiBarX - Global Pi Barter Real-Price Index
 * Frontend Application Controller
 */

let allBarters = [];
let allCommodities = [];
let allCountries = [];
let activeFilterCountry = "";
let activeFilterCommodity = "";

document.addEventListener("DOMContentLoaded", () => {
  console.log("[PiBarX] Initializing Obsidian Parity Terminal...");

  initNavTabs();
  initCalculator();
  initSubmitModal();
  initPiIntegration();
  loadAllData();

  // Auto-refresh summary data every 30 seconds
  setInterval(loadSummary, 30000);
});

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
    const data = await res.json();

    // Master Hero Metrics
    document.getElementById("hero-median-price").textContent = `$${data.global_median_pi_usd.toFixed(2)}`;
    document.getElementById("hero-delta-pct").textContent = `↑ +${data.change_24h_pct}% 24h`;
    document.getElementById("ticker-pi-rate").textContent = `$${data.global_median_pi_usd.toFixed(2)}`;
    document.getElementById("ticker-vol-pi").textContent = `${data.total_volume_24h_pi.toLocaleString()} π`;
    document.getElementById("ticker-vol-usd").textContent = `$${(data.total_volume_24h_usd / 1000000).toFixed(2)}M`;
    document.getElementById("ticker-barters-count").textContent = data.total_barters_count;
    document.getElementById("ticker-sync-status").textContent = data.last_block_sync;

    document.getElementById("kpi-volume-pi").textContent = `${data.total_volume_24h_pi.toLocaleString()} π`;
    document.getElementById("kpi-volume-usd").textContent = `≈ $${(data.total_volume_24h_usd / 1000000).toFixed(2)}M USD`;
    document.getElementById("kpi-active-countries").textContent = `${data.active_countries_count} Countries`;
    document.getElementById("kpi-confidence").textContent = `${data.confidence_score}%`;
    document.getElementById("kpi-gcv-div").textContent = `${data.gcv_divergence_pct}%`;
  } catch (err) {
    console.error("[PiBarX] Error loading summary:", err);
  }
}

async function loadCommodities() {
  try {
    const res = await fetch("/api/commodities");
    allCommodities = await res.json();
    renderCommodityGrid(allCommodities);
    populateCommodityDropdowns(allCommodities);
  } catch (err) {
    console.error("[PiBarX] Error loading commodities:", err);
  }
}

function renderCommodityGrid(commodities) {
  const container = document.getElementById("commodity-cards-container");
  if (!container) return;

  container.innerHTML = commodities.map(c => `
    <div class="comm-card" onclick="selectCommodityForCalc('${c.id}')">
      <div class="comm-top">
        <div class="comm-icon-box">${c.icon}</div>
        <span class="comm-tag">${c.symbol} INDEX</span>
      </div>
      <div class="comm-name">${c.name}</div>
      <div class="comm-unit">${c.unit}</div>
      <div class="comm-metrics">
        <div>
          <div class="comm-metric-label">Median Barter</div>
          <div class="comm-metric-val font-mono" style="color: var(--pi-purple-light);">${c.median_pi_price} π</div>
        </div>
        <div>
          <div class="comm-metric-label">Implied Rate</div>
          <div class="comm-metric-val font-mono" style="color: var(--yield-emerald-light);">$${c.implied_pi_usd.toFixed(2)}</div>
        </div>
      </div>
      <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 11px; color: var(--text-dim);">
        <span>Benchmark: $${c.benchmark_usd.toFixed(2)}</span>
        <span class="pill-delta delta-up">↑ +${c.change_24h_pct}%</span>
      </div>
    </div>
  `).join("");
}

async function loadCountries() {
  try {
    const res = await fetch("/api/countries");
    allCountries = await res.json();
    renderCountryTable(allCountries);
    populateCountryDropdowns(allCountries);
  } catch (err) {
    console.error("[PiBarX] Error loading countries:", err);
  }
}

function renderCountryTable(countries) {
  const tbody = document.getElementById("country-table-body");
  if (!tbody) return;

  tbody.innerHTML = countries.map((c, i) => {
    let consensusBadge = "";
    if (c.consensus_level === "HIGH") {
      consensusBadge = `<span class="badge-status status-onchain">Consensus Tinggi</span>`;
    } else if (c.consensus_level === "MODERATE") {
      consensusBadge = `<span class="badge-status status-audited">Konsensus Sedang</span>`;
    } else {
      consensusBadge = `<span class="badge-status" style="background: rgba(244,63,94,0.15); color: #f43f5e; border: 1px solid rgba(244,63,94,0.3);">Terfragmentasi</span>`;
    }

    return `
      <tr>
        <td class="font-mono" style="color: var(--text-dim);">${i + 1}</td>
        <td>
          <span style="font-size: 16px; margin-right: 6px;">${c.flag}</span>
          <strong>${c.country_name}</strong>
          <span class="brand-tag" style="margin-left: 6px;">${c.currency_code}</span>
        </td>
        <td class="font-mono" style="font-weight: 600; color: var(--yield-emerald-light);">$${c.median_barter_pi_usd.toFixed(2)}</td>
        <td class="font-mono">
          ${c.purchasing_power_ratio}x 
          <span style="font-size: 11px; color: var(--text-dim);">(vs Global)</span>
        </td>
        <td class="font-mono">${c.total_barters} trades</td>
        <td><span class="brand-tag">${c.most_popular_commodity}</span></td>
        <td>${consensusBadge}</td>
      </tr>
    `;
  }).join("");
}

async function loadBarters() {
  try {
    let url = "/api/barters?limit=50";
    if (activeFilterCountry) url += `&country=${encodeURIComponent(activeFilterCountry)}`;
    if (activeFilterCommodity) url += `&commodity=${encodeURIComponent(activeFilterCommodity)}`;

    const res = await fetch(url);
    allBarters = await res.json();
    renderBarterTable(allBarters);
  } catch (err) {
    console.error("[PiBarX] Error loading barters:", err);
  }
}

function renderBarterTable(barters) {
  const tbody = document.getElementById("barter-table-body");
  if (!tbody) return;

  if (barters.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 24px; color: var(--text-dim);">No verified barter records matching filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = barters.map(b => {
    const isTxValid = b.tx_hash && b.tx_hash.length === 64;
    const txBadge = isTxValid
      ? `<a href="https://api.mainnet.minepi.com/transactions/${b.tx_hash}" target="_blank" class="tx-hash-link" title="Verify on Pi Horizon Node">${b.tx_hash.substring(0, 8)}...${b.tx_hash.substring(56)} ↗</a>`
      : `<span style="color: var(--text-dim); font-size: 11px;">P2P Handshake</span>`;

    const statusBadge = b.verification_status === "VERIFIED_ONCHAIN"
      ? `<span class="badge-status status-onchain">● Verified On-Chain</span>`
      : `<span class="badge-status status-audited">◌ Community Audited</span>`;

    return `
      <tr>
        <td class="font-mono" style="font-size: 11px; color: var(--text-dim);">${b.timestamp.substring(5, 16)}</td>
        <td>
          <div style="font-weight: 600; color: #fff;">${b.item_name}</div>
          <div style="font-size: 11px; color: var(--text-dim);">${b.city}, ${b.country_code} • ${b.merchant_name}</div>
        </td>
        <td><span class="brand-tag">${b.commodity_id.toUpperCase()}</span></td>
        <td class="font-mono" style="font-weight: 700; color: var(--pi-purple-light);">${b.pi_amount} π</td>
        <td class="font-mono">${b.fiat_currency} ${b.fiat_value.toLocaleString()} <span style="font-size: 11px; color: var(--text-dim);">(≈ $${b.fiat_usd})</span></td>
        <td class="font-mono" style="font-weight: 600; color: var(--yield-emerald-light);">$${b.implied_pi_usd.toFixed(2)}</td>
        <td>
          ${statusBadge}
          <div style="margin-top: 4px;">${txBadge}</div>
        </td>
      </tr>
    `;
  }).join("");
}

// ==========================================
// CALCULATOR & CONVERTER
// ==========================================

function initCalculator() {
  const fiatInput = document.getElementById("calc-fiat-amount");
  const fiatCurr = document.getElementById("calc-fiat-currency");
  const commSelect = document.getElementById("calc-commodity-select");

  if (fiatInput) {
    fiatInput.addEventListener("input", runCalculator);
  }
  if (fiatCurr) {
    fiatCurr.addEventListener("change", runCalculator);
  }
  if (commSelect) {
    commSelect.addEventListener("change", (e) => {
      if (e.target.value) {
        if (fiatInput) fiatInput.value = "";
      }
      runCalculator();
    });
  }

  // Initial calculation
  runCalculator();
}

async function runCalculator() {
  const fiatInput = document.getElementById("calc-fiat-amount");
  const fiatCurr = document.getElementById("calc-fiat-currency");
  const commSelect = document.getElementById("calc-commodity-select");

  let url = "/api/calculator?";
  if (commSelect && commSelect.value) {
    url += `commodity_id=${encodeURIComponent(commSelect.value)}`;
  } else if (fiatInput && fiatInput.value) {
    url += `fiat_amount=${encodeURIComponent(fiatInput.value)}&fiat_currency=${encodeURIComponent(fiatCurr.value)}`;
  } else {
    url += `fiat_amount=100&fiat_currency=USD`;
  }

  try {
    const res = await fetch(url);
    const data = await res.json();

    document.getElementById("calc-fair-pi").textContent = `${data.recommended_pi_range.median_fair_pi} π`;
    document.getElementById("calc-cons-pi").textContent = `${data.recommended_pi_range.conservative_pi} π`;
    document.getElementById("calc-opt-pi").textContent = `${data.recommended_pi_range.optimistic_pi} π`;
    document.getElementById("calc-formula-note").textContent = data.recommended_pi_range.formula;

    document.getElementById("calc-rice-eq").textContent = `${data.purchasing_power_equivalent.kg_of_rice} kg Beras`;
    document.getElementById("calc-coffee-eq").textContent = `${data.purchasing_power_equivalent.cups_of_coffee} Cangkir Kopi`;
    document.getElementById("calc-fuel-eq").textContent = `${data.purchasing_power_equivalent.liters_of_fuel} L BBM`;

    document.getElementById("calc-gcv-contrast").textContent = `${data.gcv_comparison.gcv_amount_pi} π (GCV $314k) • Realitas konsensus: ${data.gcv_comparison.reality_multiple}`;
  } catch (err) {
    console.error("[PiBarX] Calculator error:", err);
  }
}

function selectCommodityForCalc(commId) {
  const commSelect = document.getElementById("calc-commodity-select");
  const fiatInput = document.getElementById("calc-fiat-amount");
  if (commSelect) {
    commSelect.value = commId;
  }
  if (fiatInput) {
    fiatInput.value = "";
  }
  switchTab("calculator");
  runCalculator();
}

// ==========================================
// SUBMIT BARTER MODAL
// ==========================================

function initSubmitModal() {
  const modal = document.getElementById("submit-modal");
  const openBtn = document.getElementById("open-submit-modal-btn");
  const closeBtn = document.getElementById("close-submit-modal-btn");
  const form = document.getElementById("submit-barter-form");

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      if (modal) modal.style.display = "flex";
    });
  }
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      if (modal) modal.style.display = "none";
    });
  }
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.style.display = "none";
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const statusEl = document.getElementById("submit-status-msg");
      statusEl.textContent = "Verifying with Pi Mainnet blockchain...";
      statusEl.style.color = "var(--pi-purple-light)";

      const payload = {
        item_name: document.getElementById("form-item-name").value,
        commodity_id: document.getElementById("form-commodity-id").value,
        country_code: document.getElementById("form-country-code").value,
        city: document.getElementById("form-city").value,
        merchant_name: document.getElementById("form-merchant-name").value,
        pi_amount: parseFloat(document.getElementById("form-pi-amount").value),
        fiat_value: parseFloat(document.getElementById("form-fiat-value").value),
        fiat_currency: document.getElementById("form-fiat-currency").value,
        tx_hash: document.getElementById("form-tx-hash").value.trim(),
        notes: document.getElementById("form-notes").value
      };

      try {
        const res = await fetch("/api/barters/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: json.stringify(payload)
        });
        const result = await res.json();

        if (result.success) {
          statusEl.textContent = "✓ Barter successfully indexed!";
          statusEl.style.color = "var(--yield-emerald-light)";
          setTimeout(() => {
            modal.style.display = "none";
            form.reset();
            statusEl.textContent = "";
            loadAllData();
          }, 1200);
        } else {
          statusEl.textContent = "Error indexing transaction.";
          statusEl.style.color = "var(--danger-crimson)";
        }
      } catch (err) {
        statusEl.textContent = "Submission error: " + err.message;
        statusEl.style.color = "var(--danger-crimson)";
      }
    });
  }
}

// ==========================================
// NAVIGATION & TABS
// ==========================================

function initNavTabs() {
  const navBtns = document.querySelectorAll(".nav-btn[data-tab]");
  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabName = btn.getAttribute("data-tab");
      switchTab(tabName);
    });
  });

  // Country filter pills in barter feed
  const feedFilterCountry = document.getElementById("feed-filter-country");
  if (feedFilterCountry) {
    feedFilterCountry.addEventListener("change", (e) => {
      activeFilterCountry = e.target.value;
      loadBarters();
    });
  }

  const feedFilterCommodity = document.getElementById("feed-filter-commodity");
  if (feedFilterCommodity) {
    feedFilterCommodity.addEventListener("change", (e) => {
      activeFilterCommodity = e.target.value;
      loadBarters();
    });
  }

  const feedSearch = document.getElementById("feed-search-input");
  if (feedSearch) {
    let searchTimeout = null;
    feedSearch.addEventListener("input", (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        searchBarters(e.target.value);
      }, 300);
    });
  }
}

async function searchBarters(query) {
  try {
    let url = `/api/barters?limit=50&search=${encodeURIComponent(query)}`;
    if (activeFilterCountry) url += `&country=${encodeURIComponent(activeFilterCountry)}`;
    if (activeFilterCommodity) url += `&commodity=${encodeURIComponent(activeFilterCommodity)}`;
    const res = await fetch(url);
    const data = await res.json();
    renderBarterTable(data);
  } catch (err) {
    console.error(err);
  }
}

function switchTab(tabName) {
  // Update nav buttons
  document.querySelectorAll(".nav-btn[data-tab]").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabName);
  });

  // Scroll to section or toggle view
  const targetSec = document.getElementById(`section-${tabName}`);
  if (targetSec) {
    targetSec.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function populateCommodityDropdowns(commodities) {
  const calcSelect = document.getElementById("calc-commodity-select");
  const formSelect = document.getElementById("form-commodity-id");
  const feedFilter = document.getElementById("feed-filter-commodity");

  const opts = commodities.map(c => `<option value="${c.id}">${c.icon} ${c.name} (${c.unit})</option>`).join("");

  if (calcSelect) calcSelect.innerHTML = `<option value="">Select standard basket...</option>` + opts;
  if (formSelect) formSelect.innerHTML = opts;
  if (feedFilter) feedFilter.innerHTML = `<option value="">All Commodities</option>` + opts;
}

function populateCountryDropdowns(countries) {
  const formCountry = document.getElementById("form-country-code");
  const feedCountry = document.getElementById("feed-filter-country");

  const opts = countries.map(c => `<option value="${c.country_code}">${c.flag} ${c.country_name} (${c.currency_code})</option>`).join("");

  if (formCountry) formCountry.innerHTML = opts;
  if (feedCountry) feedCountry.innerHTML = `<option value="">All Countries</option>` + opts;
}



// ==========================================
// PI NETWORK NODE & PI BROWSER SDK INTEGRATION
// ==========================================

let latestPiLedger = null;
let currentPioneer = null;

async function initPiIntegration() {
  console.log("[PiBarX] Initializing Pi Network Connection & Telemetry...");

  // 1. Fetch live telemetry from Pi Mainnet Horizon Node
  await syncPiNetworkTelemetry();
  setInterval(syncPiNetworkTelemetry, 15000); // sync every 15s

  // 2. Setup Pi SDK if running inside Pi Browser
  setupPiBrowserSDK();
}

async function syncPiNetworkTelemetry() {
  try {
    const res = await fetch("/api/pi/status");
    if (!res.ok) return;
    const data = await res.json();

    if (data.connected && data.latest_ledger) {
      latestPiLedger = data.latest_ledger;
      const statusElem = document.getElementById("ticker-sync-status");
      if (statusElem) {
        statusElem.innerHTML = `<span style="color: #10b981;">●</span> Pi Mainnet #${data.latest_ledger.toLocaleString()}`;
        statusElem.style.color = "#10b981";
      }
    }
  } catch (err) {
    console.warn("[PiBarX] Pi telemetry sync error:", err);
  }
}

function setupPiBrowserSDK() {
  const authBtn = document.getElementById("pi-auth-btn");
  const authText = document.getElementById("pi-auth-text");

  // Check if Pi SDK object exists
  const isPiBrowser = typeof window.Pi !== "undefined";

  if (isPiBrowser) {
    try {
      window.Pi.init({ version: "2.0", sandbox: false });
      console.log("[PiBarX] Pi SDK initialized for Pi Browser.");
    } catch (e) {
      console.warn("[PiBarX] Pi.init warning:", e);
    }
  }

  if (authBtn) {
    authBtn.addEventListener("click", async () => {
      if (currentPioneer) {
        alert(`Terhubung sebagai Pioneer: @${currentPioneer}\nPi Mainnet Ledger: #${latestPiLedger ? latestPiLedger.toLocaleString() : 'Active'}`);
        return;
      }

      if (typeof window.Pi !== "undefined" && window.Pi.authenticate) {
        authText.textContent = "Connecting...";
        try {
          const scopes = ["username", "payments", "wallet_address"];
          const auth = await window.Pi.authenticate(scopes, onIncompletePaymentFound);
          if (auth && auth.user) {
            currentPioneer = auth.user.username;
            authText.textContent = `@${currentPioneer}`;
            authBtn.classList.add("authenticated");
            
            // Auto fill form if opened
            const merchantInput = document.getElementById("form-merchant");
            if (merchantInput && !merchantInput.value) {
              merchantInput.value = `@${currentPioneer}`;
            }
            alert(`Berhasil terhubung ke Pi Network! Selamat datang, Pioneer @${currentPioneer}`);
          }
        } catch (err) {
          console.error("[PiBarX] Pi authentication error:", err);
          authText.textContent = "Connect Pi";
          alert("Otentikasi Pi dibatalkan atau terjadi kesalahan.");
        }
      } else {
        // Desktop browser fallback
        const msg = `⚡ PI NETWORK MAINNET NODE STATUS: ONLINE\n\n` +
          `• Horizon Node: https://api.mainnet.minepi.com\n` +
          `• Core Version: stellar-core 28.0.1\n` +
          `• Latest Ledger Sequence: #${latestPiLedger ? latestPiLedger.toLocaleString() : 'Syncing...'}\n\n` +
          `Saat ini Anda mengakses PiBarX lewat Browser Standar.\n` +
          `Untuk login dengan akun Pioneer dan dompet Pi Wallet Anda, silakan buka link ini langsung di dalam aplikasi PI BROWSER (smartphone).`;
        alert(msg);
      }
    });
  }
}

function onIncompletePaymentFound(payment) {
  console.log("[PiBarX] Incomplete payment found:", payment);
}
