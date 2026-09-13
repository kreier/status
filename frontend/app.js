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
