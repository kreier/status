"""Internet speed test. Runs every 2h per config.yaml - this is the expensive one, don't run
it more often. Logs to history (for the heatmap) in addition to the latest-value entry."""

import speedtest

from common import append_history, write_entries


def collect():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_mbps = st.download() / 1_000_000
        upload_mbps = st.upload() / 1_000_000
        ping_ms = st.results.ping
    except Exception as e:
        entries = [{"id": "speedtest", "category": "network", "label": "Internet speed",
                    "value": f"unavailable: {e}", "status": "error"}]
        write_entries(entries)
        return entries

    append_history("speedtest", {
        "download_mbps": round(download_mbps, 1),
        "upload_mbps": round(upload_mbps, 1),
        "ping_ms": round(ping_ms, 1),
    })
    entries = [{"id": "speedtest", "category": "network", "label": "Internet speed",
                "value": f"{download_mbps:.1f} / {upload_mbps:.1f} Mbps, {ping_ms:.0f} ms",
                "status": "ok"}]
    write_entries(entries)
    return entries


if __name__ == "__main__":
    print(collect())
