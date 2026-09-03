# Schema

## Collector output

Every collector produces one or more entries in this shape:

```json
{
  "id": "pi_load",
  "category": "system",
  "label": "Load average",
  "value": "0.42, 0.38, 0.35",
  "unit": null,
  "updated_at": "2026-09-03T14:22:00+07:00",
  "status": "ok"
}
```

- `id` — stable, unique, snake_case
- `category` — groups entries on the frontend (`system`, `network`, `home`, `github`, ...)
- `value` — already display-ready; formatting decisions belong in the collector, not the
  frontend
- `status` — `ok`, `stale`, or `error` — lets the frontend show a warning if a collector
  hasn't updated recently or failed

`status.json` is either a flat array of these, or an object keyed by `id` — decide in
Phase 2 and update this doc.

## Speedtest history

Separate from `status.json` — an append-only table:

```
timestamp, download_mbps, upload_mbps, ping_ms
2026-09-03T14:00:00+07:00, 84.2, 22.1, 14
```

The frontend aggregates this into a day × hour grid for the heatmap; `status.json` just
carries the latest reading.

## Hash-guard pattern

For sources that rarely change (GitHub repos, NAS image count), do a cheap check before any
expensive fetch or processing:

```python
def run_if_changed(name, fetch_fn, process_fn, state_dir="state/"):
    raw = fetch_fn()                      # cheap: API call / file listing
    new_hash = sha256(canonical(raw))     # canonical = sorted keys, stable order
    old_hash = read_hash(state_dir, name)
    if new_hash != old_hash:
        result = process_fn(raw)          # expensive: thumbnails, star diffing, etc.
        write_hash(state_dir, name, new_hash)
        write_result(state_dir, name, result)
    touch_last_checked(state_dir, name)   # cheap, always update this
```

- **GitHub**: `fetch_fn` lists repos with `pushed_at` and star count; hash the sorted
  `(name, pushed_at, stargazers_count)` tuples.
- **NAS images**: `fetch_fn` does a fast listing (file count + total size + latest mtime, not
  a full walk); hash that triple. Only do the expensive full count/categorization when it
  changes.

This helper lives in a shared module — collectors that need it import it, they don't
reimplement it.

## Config

`config.yaml` (git-ignored) holds settings that change independently of code — repo
categories, display names, collector intervals. See `config/config.example.yaml` for the
tracked template.
