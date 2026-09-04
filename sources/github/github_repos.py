"""GitHub repo list, stars, last updated. Hash-guarded: cheap metadata fetch every cycle,
expensive category/display-name mapping only redone when something actually changed."""

import os

import requests

from core.config import load_config
from core.state import run_if_changed
from core.status import write_entries

GITHUB_USER = os.environ.get("GITHUB_USERNAME", "kreier")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # optional, raises rate limit from 60/hr to 5000/hr


def fetch_repos():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{GITHUB_USER}/repos",
            params={"per_page": 100, "page": page, "sort": "updated"},
            headers=headers, timeout=15,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1

    # only the fields that matter for change detection + display - keeps the hash stable
    # and ignores fields (like fetched_at) that would change every request
    return sorted(
        [
            {"name": r["name"], "stars": r["stargazers_count"],
             "pushed_at": r["pushed_at"], "url": r["html_url"]}
            for r in repos if not r["archived"]
        ],
        key=lambda r: r["name"],
    )


def process(raw):
    config = load_config()
    meta_by_repo = config.get("repos", {})
    items = []
    for r in raw:
        meta = meta_by_repo.get(f"{GITHUB_USER}/{r['name']}", {})
        items.append({
            "name": meta.get("display_name", r["name"]),
            "category": meta.get("category", "uncategorized"),
            "stars": r["stars"],
            "updated": r["pushed_at"],
            "url": r["url"],
        })
    return items


def collect():
    result = run_if_changed("github_repos", fetch_repos, process)
    if isinstance(result, dict) and "error" in result:
        entries = [{"id": "github_repos", "category": "github", "label": "Repositories",
                    "value": f"unavailable: {result['error']}", "status": "error"}]
    else:
        entries = [{"id": "github_repos", "category": "github", "label": "Repositories",
                    "value": result, "status": "ok"}]
    write_entries(entries)
    return entries


if __name__ == "__main__":
    print(collect())
