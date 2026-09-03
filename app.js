const POLL_MS = 60_000;

async function loadStatus() {
  try {
    const res = await fetch("data/status.json", { cache: "no-store" });
    const entries = await res.json();
    render(entries);
    document.getElementById("last-updated").textContent =
      `Updated ${new Date().toLocaleTimeString()}`;
  } catch (err) {
    document.getElementById("last-updated").textContent = "Unable to load status.json";
  }
}

function render(entries) {
  const root = document.getElementById("cards");
  root.innerHTML = "";

  const byCategory = {};
  for (const e of entries) {
    (byCategory[e.category] ??= []).push(e);
  }

  for (const [category, items] of Object.entries(byCategory)) {
    const section = document.createElement("section");
    const heading = document.createElement("h2");
    heading.textContent = category;
    section.appendChild(heading);

    const grid = document.createElement("div");
    grid.className = "grid";

    for (const item of items) {
      grid.appendChild(renderCard(item));
    }

    section.appendChild(grid);
    root.appendChild(section);
  }
}

function renderCard(item) {
  const card = document.createElement("div");
  card.className = `card status-${item.status}`;

  const title = document.createElement("h3");
  title.textContent = item.label;
  card.appendChild(title);

  if (item.id === "github_repos" && Array.isArray(item.value)) {
    for (const repo of item.value) {
      const row = document.createElement("div");
      row.className = "repo";
      row.innerHTML = `
        <a href="${repo.url}" target="_blank" rel="noopener">${repo.name}</a>
        <span class="meta">${repo.category} &middot; \u2605 ${repo.stars} &middot; ${new Date(repo.updated).toLocaleDateString()}</span>
      `;
      card.appendChild(row);
    }
  } else {
    const value = document.createElement("p");
    value.className = "value";
    value.textContent = item.value;
    card.appendChild(value);
  }

  return card;
}

loadStatus();
setInterval(loadStatus, POLL_MS);
