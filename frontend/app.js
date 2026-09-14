// Dynamic base path resolver: handles direct access, /status, and reverse proxies like Traefik
function getBaseUrl() {
  let path = window.location.pathname;
  if (path.endsWith("/index.html")) {
    path = path.slice(0, -11);
  }
  return path.replace(/\/+$/, "");
}

function apiUrl(endpoint) {
  const base = getBaseUrl();
  return `${base}/api/${endpoint}`.replace(/\/+/g, "/");
}

// In-memory cache for uptime history to prevent redundant network requests
const historyCache = {
  364: null,
  90: null,
};

async function loadStatus() {
  const lastUpdatedEl = document.getElementById("last-updated");
  const url = apiUrl("status");
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    render(data);
    if (lastUpdatedEl) {
      lastUpdatedEl.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    }
  } catch (err) {
    console.error(`[status] Failed to fetch ${url}:`, err);
    if (lastUpdatedEl) {
      lastUpdatedEl.textContent = "Offline / Connection error";
    }
  }
}

function render(data) {
  if (!data) return;

  const machineName = data.machine || "Machine";
  document.title = `${machineName} Status`;

  setText("machine-name", machineName);

  if (data.system) {
    setText("system-os", data.system.os || "--");
    setText("kernel-version", data.system.kernel || "--");
    setText("architecture", data.system.architecture || "--");
    setText("uptime", data.system.uptime || "--");
  }

  // Handle tuptime stats
  const rowLife = document.getElementById("row-system-life");
  const rowUptime = document.getElementById("row-system-uptime");
  if (data.tuptime && data.tuptime.available) {
    if (rowLife) {
      rowLife.style.display = "flex";
      setText("system-life", `${data.tuptime.system_life} (${data.tuptime.startups} starts)`);
      const valLife = document.getElementById("system-life");
      if (valLife) {
        valLife.title = `Startups: ${data.tuptime.startups}, Shutdowns: ${data.tuptime.shutdowns_formatted}`;
      }
    }
    if (rowUptime) {
      rowUptime.style.display = "flex";
      setText("system-uptime-rate", `${data.tuptime.uptime_rate_formatted}`);
      const valUptime = document.getElementById("system-uptime-rate");
      if (valUptime) {
        valUptime.title = `Total up: ${data.tuptime.total_uptime}, Total down: ${data.tuptime.total_downtime}`;
      }
    }
  } else {
    // Show System life as not available
    if (rowLife) {
      rowLife.style.display = "flex";
      setText("system-life", "not available");
      const valLife = document.getElementById("system-life");
      if (valLife) {
        valLife.title = (data.tuptime && data.tuptime.reason) ? data.tuptime.reason : "Mount /var/lib/tuptime in docker-compose.yml";
      }
    }
    if (rowUptime) {
      rowUptime.style.display = "none";
    }
  }

  if (data.versions) {
    setText("app-version", data.versions.application || "--");
    setText("status-version", data.versions.status || "--");
    setText("updater-version", data.versions.updater || "--");
  }

  if (data.updates) {
    const badge = document.getElementById("updates-available");
    if (badge) {
      const isYes = data.updates.available || data.updates.status_text === "YES";
      badge.textContent = isYes ? "YES" : "NO";
      badge.className = `update-badge ${isYes ? "badge-yes" : "badge-no"}`;
    }
  }

  // Update API link
  const apiLink = document.getElementById("api-link");
  if (apiLink) {
    apiLink.href = apiUrl("status");
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function showFeedback(text, isError = false) {
  const fb = document.getElementById("action-feedback");
  if (!fb) return;
  fb.textContent = text;
  fb.className = `action-feedback visible ${isError ? "error" : "success"}`;
  setTimeout(() => {
    fb.className = "action-feedback";
  }, 4000);
}

// Toggle extra card boxes below the floating status badge
function toggleCard(cardId) {
  const cardEl = document.getElementById(`card-${cardId === "grid" ? "availability-grid" : "timeline"}`);
  const btnEl = document.getElementById(`btn-toggle-${cardId}`);
  if (!cardEl) return;

  const isVisible = cardEl.style.display !== "none";
  const nextVisible = !isVisible;
  cardEl.style.display = nextVisible ? "block" : "none";

  if (btnEl) {
    btnEl.classList.toggle("active", nextVisible);
  }

  if (nextVisible) {
    if (cardId === "grid") {
      loadAndRenderMultiYearGrid();
    } else if (cardId === "timeline") {
      loadAndRenderTimeline();
    }
    setTimeout(() => {
      cardEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 50);
  }
}
window.toggleCard = toggleCard;

async function fetchHistory(query) {
  const cacheKey = typeof query === "string" ? query : String(query);
  if (historyCache[cacheKey]) {
    return historyCache[cacheKey];
  }
  try {
    const res = await fetch(apiUrl(`history?${cacheKey.startsWith("year") || cacheKey.startsWith("days") ? cacheKey : "days=" + cacheKey}`));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    historyCache[cacheKey] = data;
    return data;
  } catch (err) {
    console.error(`[status] Failed to fetch history (${query}):`, err);
    return null;
  }
}

async function loadAndRenderMultiYearGrid() {
  const data = await fetchHistory("year=all");
  renderMultiYearGrid(data);
}

async function loadAndRenderTimeline() {
  const data = await fetchHistory("days=90");
  renderTimeline(data);
}

function renderMultiYearGrid(data) {
  const container = document.getElementById("multi-year-grid-container");
  if (!container) return;

  const countBadge = document.getElementById("grid-years-count");

  if (!data || !data.available || !data.years || data.years.length === 0) {
    if (countBadge) countBadge.textContent = "0 Years";
    container.innerHTML = `
      <div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.8rem; width: 100%;">
        Tuptime history is not available.<br>
        <span style="font-size: 0.72rem;">Mount <code>/var/lib/tuptime</code> in docker-compose.yml to enable.</span>
      </div>`;
    updateGridTooltip("Tuptime database not mounted or empty.", "unrecorded");
    return;
  }

  if (countBadge) {
    countBadge.textContent = `${data.years.length} Year${data.years.length !== 1 ? "s" : ""}`;
  }

  container.innerHTML = "";
  const currentYear = new Date().getFullYear();

  data.years.forEach((yr) => {
    const yrInfo = data.yearly && data.yearly[String(yr)];
    if (!yrInfo || !yrInfo.history) return;

    const block = document.createElement("div");
    block.className = "year-block";

    const header = document.createElement("div");
    header.className = "year-header";

    const title = document.createElement("span");
    title.className = "year-title";
    title.textContent = yr === currentYear ? `${yr} (YTD)` : `${yr}`;

    const meta = document.createElement("div");
    meta.className = "year-meta";
    meta.innerHTML = `
      <span class="year-rate">${yrInfo.overall_rate_formatted} uptime</span>
      <span class="year-badge">${yrInfo.total_bad_shutdowns} bad stop${yrInfo.total_bad_shutdowns !== 1 ? "s" : ""}</span>
    `;

    header.appendChild(title);
    header.appendChild(meta);
    block.appendChild(header);

    const scrollWrap = document.createElement("div");
    scrollWrap.className = "heatmap-scroll";

    const grid = document.createElement("div");
    grid.className = "heatmap-grid";

    const history = yrInfo.history;
    const weeks = Math.ceil(history.length / 7);

    for (let w = 0; w < weeks; w++) {
      const col = document.createElement("div");
      col.className = "heat-col";
      for (let d = 0; d < 7; d++) {
        const idx = w * 7 + d;
        if (idx >= history.length) break;
        const item = history[idx];
        const cell = document.createElement("div");
        cell.className = "heat-cell";

        let heatClass = "heat-full";
        if (item.status === "future") {
          heatClass = "heat-future";
        } else if (item.status === "unrecorded" || item.uptime_pct === null) {
          heatClass = "heat-unrecorded";
        } else if (item.uptime_pct >= 99.5) {
          heatClass = "heat-full";
        } else if (item.uptime_pct >= 95.0) {
          heatClass = "heat-high";
        } else if (item.uptime_pct >= 80.0) {
          heatClass = "heat-med";
        } else if (item.uptime_pct > 0.0) {
          heatClass = "heat-low";
        } else {
          heatClass = "heat-none";
        }
        cell.classList.add(heatClass);

        if (item.status !== "future") {
          const hours = (item.uptime_seconds / 3600).toFixed(1);
          const pctStr = item.uptime_pct !== null ? `${item.uptime_pct}%` : "No data";
          const badStr = item.bad_shutdowns > 0 ? ` &middot; ${item.bad_shutdowns} bad stop${item.bad_shutdowns > 1 ? "s" : ""}` : "";
          const tooltipMsg = `${item.date}: ${pctStr} uptime (${hours}h)${badStr}`;

          cell.addEventListener("mouseenter", () => updateGridTooltip(tooltipMsg, item.status));
          cell.addEventListener("click", () => updateGridTooltip(tooltipMsg, item.status));
        }

        col.appendChild(cell);
      }
      grid.appendChild(col);
    }

    scrollWrap.appendChild(grid);
    block.appendChild(scrollWrap);
    container.appendChild(block);
  });
}

function updateGridTooltip(htmlContent, status) {
  const tip = document.getElementById("grid-tooltip");
  if (!tip) return;
  const badgeColor = status === "offline" ? "#ef4444" : (status === "unrecorded" ? "#71717a" : "#10b981");
  const badgeText = status ? status.toUpperCase() : "OK";
  tip.innerHTML = `<span>${htmlContent}</span><span style="font-family:monospace; font-size:0.68rem; color:${badgeColor}; font-weight:600;">${badgeText}</span>`;
}

function renderTimeline(data) {
  const container = document.getElementById("timeline-bars-container");
  if (!container) return;

  const statusSummary = document.getElementById("timeline-status-summary");

  if (!data || !data.available || !data.history || data.history.length === 0) {
    setText("timeline-rate", "--");
    setText("timeline-incidents", "--");
    if (statusSummary) {
      statusSummary.textContent = "Unavailable";
      statusSummary.style.color = "#71717a";
    }
    container.innerHTML = `
      <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.8rem; width: 100%;">
        Tuptime history is not available.<br>
        <span style="font-size: 0.72rem;">Mount <code>/var/lib/tuptime</code> in docker-compose.yml to enable.</span>
      </div>`;
    updateTimelineTooltip("Tuptime database not mounted or empty.", "unrecorded");
    return;
  }

  setText("timeline-rate", data.overall_rate_formatted || "--");
  const badStops = data.total_bad_shutdowns || 0;
  setText("timeline-incidents", `${badStops} bad stop${badStops !== 1 ? "s" : ""}`);

  if (statusSummary) {
    if (badStops === 0 && data.overall_rate >= 99.9) {
      statusSummary.textContent = "Operational";
      statusSummary.style.color = "#10b981";
    } else if (data.overall_rate >= 98.0) {
      statusSummary.textContent = "Degraded / Minor Outages";
      statusSummary.style.color = "#f59e0b";
    } else {
      statusSummary.textContent = "Outages Detected";
      statusSummary.style.color = "#ef4444";
    }
  }

  container.innerHTML = "";
  data.history.forEach((item) => {
    const bar = document.createElement("div");
    bar.className = "timeline-bar";

    if (item.uptime_pct === null) {
      bar.style.backgroundColor = "transparent";
      bar.style.border = "1px dashed var(--border)";
    } else if (item.bad_shutdowns > 0) {
      bar.style.backgroundColor = "#ef4444";
    } else if (item.uptime_pct >= 99.5) {
      bar.style.backgroundColor = "#10b981";
    } else if (item.uptime_pct >= 95.0) {
      bar.style.backgroundColor = "#34d399";
    } else if (item.uptime_pct >= 80.0) {
      bar.style.backgroundColor = "#f59e0b";
    } else {
      bar.style.backgroundColor = "#3f3f46";
    }

    const hours = (item.uptime_seconds / 3600).toFixed(1);
    const pctStr = item.uptime_pct !== null ? `${item.uptime_pct}%` : "No data";
    const badStr = item.bad_shutdowns > 0 ? ` &middot; ${item.bad_shutdowns} bad stop${item.bad_shutdowns > 1 ? "s" : ""}` : "";
    const tooltipMsg = `${item.date}: ${pctStr} uptime (${hours}h)${badStr}`;

    bar.addEventListener("mouseenter", () => updateTimelineTooltip(tooltipMsg, item.bad_shutdowns > 0 ? "warning" : "ok"));
    bar.addEventListener("click", () => updateTimelineTooltip(tooltipMsg, item.bad_shutdowns > 0 ? "warning" : "ok"));
    container.appendChild(bar);
  });
}

function updateTimelineTooltip(htmlContent, status) {
  const tip = document.getElementById("timeline-tooltip");
  if (!tip) return;
  const badgeColor = status === "warning" ? "#ef4444" : (status === "unrecorded" ? "#71717a" : "#10b981");
  const badgeText = status === "warning" ? "INCIDENT" : (status === "unrecorded" ? "UNRECORDED" : "OPERATIONAL");
  tip.innerHTML = `<span>${htmlContent}</span><span style="font-family:monospace; font-size:0.68rem; color:${badgeColor}; font-weight:600;">${badgeText}</span>`;
}

function init() {
  const btnCheck = document.getElementById("btn-check");
  const btnUpdate = document.getElementById("btn-update");

  if (btnCheck) {
    btnCheck.addEventListener("click", async () => {
      btnCheck.disabled = true;
      showFeedback("Checking for updates...");
      try {
        const res = await fetch(apiUrl("check"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        render(data);
        showFeedback(data.updates?.message || "Check complete.");
      } catch (err) {
        showFeedback("Check failed: " + err.message, true);
      } finally {
        btnCheck.disabled = false;
      }
    });
  }

  if (btnUpdate) {
    btnUpdate.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to trigger an update?")) return;
      btnUpdate.disabled = true;
      showFeedback("Triggering update...");
      try {
        const res = await fetch(apiUrl("update"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        showFeedback(data.message || "Update triggered successfully.");
        // Refresh status after update trigger
        setTimeout(loadStatus, 2000);
      } catch (err) {
        showFeedback("Update failed: " + err.message, true);
      } finally {
        btnUpdate.disabled = false;
      }
    });
  }

  // Initial load
  loadStatus();
  // Poll every 60s
  setInterval(loadStatus, 60000);
}

// Ensure init() always executes even if DOMContentLoaded already fired
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
