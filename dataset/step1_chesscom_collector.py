#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import signal
import time
from pathlib import Path

import requests
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    generate_latest,
    start_http_server,
)

# =========================
# Config / constants
# =========================
DEFAULT_UA = os.getenv("COLLECTOR_USER_AGENT", "DeepChessIQ-collector/0.1")
BASE = "https://api.chess.com/pub"
SITE = "chesscom"

OUT_DIR = Path("data/chesscom/filtered")
OUT_DIR.mkdir(parents=True, exist_ok=True)
GM_OUT = OUT_DIR / "chesscom_GM_all.pgn"

RUN_START_TS = time.time()

# =========================
# Prometheus metrics
# =========================
REQS_TOTAL = Counter(
    "scrape_requests_total",
    "Total HTTP requests issued",
    ["site", "endpoint"],
)
ERRS_TOTAL = Counter(
    "scrape_errors_total",
    "Total errors by type",
    ["site", "endpoint", "error_type"],
)
RESP_TIME = Histogram(
    "scrape_response_time_seconds",
    "HTTP response time seconds",
    ["site", "endpoint"],
)
PAGES_ATTEMPTED = Counter(
    "scrape_pages_attempted_total",
    "Game pages attempted (post-JSON parse)",
    ["site", "endpoint", "bucket", "title"],
)
PAGES_SCRAPED = Counter(
    "scrape_pages_scraped_total",
    "Game pages successfully written",
    ["site", "endpoint", "bucket", "title"],
)
MISSING_FIELD = Counter(
    "scrape_missing_field_total",
    "Missing expected fields while processing",
    ["site", "endpoint", "field"],
)
IP_BLOCKS = Counter(
    "scrape_ip_blocks_total",
    "IP block/captcha/429 occurrences",
    ["site"],
)
BUCKET_FILL = Gauge(
    "scrape_bucket_fill",
    "Per-bucket written count (for display; GM has single sink)",
    ["site", "bucket", "group"],
)

# For GM gauge updates without peeking internals
GM_WRITTEN = 0
GM_GAUGE = BUCKET_FILL.labels(SITE, "GM_all", "GM")
GM_GAUGE.set(0)


# =========================
# Helpers
# =========================
def backoff_delay(attempt: int, base=0.5, mult=2.0, max_delay=60.0) -> float:
    """Exponential backoff with ±20% jitter."""
    delay = min(max_delay, base * (mult ** (attempt - 1)))
    jitter = 0.8 + 0.4 * (os.urandom(1)[0] / 255.0)
    return delay * jitter


def bucket_label(w, b) -> str:
    """1500–1599, …, 2900–2999; else 'NA'."""
    try:
        avg = (int(w) + int(b)) // 2
    except Exception:
        return "NA"
    if avg < 1500 or avg > 2999:
        return "NA"
    lo = max(1500, min(2900, (avg // 100) * 100))
    return f"{lo}-{lo+99}"


def hash_game(g: dict, pgn: str) -> str:
    """Stable-ish hash across retries/sources."""
    site = g.get("url", "")
    end_time = str(g.get("end_time", ""))
    result = g.get("white", {}).get("result", "") + "-" + g.get("black", {}).get(
        "result", ""
    )
    movetext = pgn.split("\n\n", 1)[-1]
    prefix = " ".join(movetext.split()[:60])
    return hashlib.sha1(f"{site}|{end_time}|{result}|{prefix}".encode("utf-8")).hexdigest()


class Seen:
    def __init__(self):
        self._set = set()

    def has(self, h: str) -> bool:
        return h in self._set

    def add(self, h: str):
        self._set.add(h)


def fetch_json(endpoint: str, url: str, session: requests.Session, attempts=5):
    """GET with retries, metrics, and error typing."""
    for a in range(1, attempts + 1):
        REQS_TOTAL.labels(SITE, endpoint).inc()
        start = time.time()
        try:
            r = session.get(url, timeout=30)
        except (requests.Timeout, requests.ConnectionError):
            RESP_TIME.labels(SITE, endpoint).observe(time.time() - start)
            ERRS_TOTAL.labels(SITE, endpoint, "timeout").inc()
            time.sleep(backoff_delay(a))
            continue

        RESP_TIME.labels(SITE, endpoint).observe(time.time() - start)

        if r.status_code == 429:
            IP_BLOCKS.labels(SITE).inc()
            ERRS_TOTAL.labels(SITE, endpoint, "blocked").inc()
            ra = r.headers.get("Retry-After")
            delay = int(ra) if (ra and ra.isdigit()) else backoff_delay(a)
            time.sleep(delay)
            continue

        if 500 <= r.status_code < 600:
            ERRS_TOTAL.labels(SITE, endpoint, "5xx").inc()
            time.sleep(backoff_delay(a))
            continue

        if r.status_code == 404:
            ERRS_TOTAL.labels(SITE, endpoint, "404").inc()
            return None

        try:
            r.raise_for_status()
        except requests.HTTPError:
            ERRS_TOTAL.labels(SITE, endpoint, f"http_{r.status_code}").inc()
            return None

        try:
            return r.json()
        except ValueError:
            ERRS_TOTAL.labels(SITE, endpoint, "json_error").inc()
            if a < 3:
                time.sleep(backoff_delay(a))
                continue
            return None
    return None


def write_pgn_append(path: Path, pgn_block: str):
    """Simple append; we run single-threaded."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(pgn_block.rstrip("\n") + "\n\n")


def process_month_games(data: dict, title: str, seen: Seen):
    """Process one monthly archive JSON."""
    global GM_WRITTEN
    games = data.get("games", []) if isinstance(data, dict) else []
    for g in games:
        w = g.get("white", {}).get("rating")
        b = g.get("black", {}).get("rating")
        rules = g.get("rules")
        rated = g.get("rated", False)
        pgn = g.get("pgn")

        bkt = bucket_label(w, b)
        PAGES_ATTEMPTED.labels(SITE, "monthly_archive", bkt, title).inc()

        # Field presence checks
        missing = False
        if not pgn:
            MISSING_FIELD.labels(SITE, "monthly_archive", "pgn").inc()
            missing = True
        if w is None:
            MISSING_FIELD.labels(SITE, "monthly_archive", "white.rating").inc()
            missing = True
        if b is None:
            MISSING_FIELD.labels(SITE, "monthly_archive", "black.rating").inc()
            missing = True
        if missing:
            continue

        # Filters
        if rules != "chess":
            continue
        if not rated:
            continue

        # Dedupe
        h = hash_game(g, pgn)
        if seen.has(h):
            continue
        seen.add(h)

        # GM path only (Step 1)
        write_pgn_append(GM_OUT, pgn)
        PAGES_SCRAPED.labels(SITE, "monthly_archive", bkt, title).inc()
        GM_WRITTEN += 1
        GM_GAUGE.set(GM_WRITTEN)


# =========================
# Metrics snapshotting
# =========================
def _quantile_from_buckets(buckets, total_count, q):
    """
    buckets: list of (le_value, cumulative_count)
    returns the le threshold approximating the q-quantile
    """
    if total_count <= 0:
        return None
    need = total_count * q
    # sort by le (handle '+Inf')
    def to_float(x):
        try:
            return float(x)
        except Exception:
            return float("inf")

    for le, c in sorted(buckets, key=lambda kv: to_float(kv[0])):
        if c >= need:
            try:
                return float(le)
            except Exception:
                return None
    return None


def save_metrics_snapshot(metrics_dir: str, run_name: str, run_start_ts: float):
    out_dir = Path(metrics_dir) / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Prometheus exposition text
    expo = generate_latest(REGISTRY).decode("utf-8")
    (out_dir / "metrics.prom").write_text(expo, encoding="utf-8")

    # 2) Flat samples CSV
    rows = []
    for m in REGISTRY.collect():
        for s in m.samples:  # name, labels, value
            rows.append(
                {
                    "metric": m.name,
                    "sample": s.name,
                    "labels": json.dumps(s.labels, sort_keys=True),
                    "value": s.value,
                }
            )
    with open(out_dir / "metrics_samples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "sample", "labels", "value"])
        w.writeheader()
        w.writerows(rows)

    # 3) KPI summary (overall + per-endpoint)
    def sum_counter(name, where=lambda lab: True):
        tot = 0.0
        for m in REGISTRY.collect():
            for s in m.samples:
                # sample names are like 'scrape_requests_total'
                if s.name == name and where(s.labels):
                    tot += float(s.value)
        return tot


    # Latency histogram rollup per endpoint
    lat = {}  # endpoint -> {"sum":x, "count":y, "b":{le:cum}}
    for m in REGISTRY.collect():
        if m.name != "scrape_response_time_seconds":
            continue
        for s in m.samples:
            ep = s.labels.get("endpoint", "unknown")
            L = lat.setdefault(ep, {"sum": 0.0, "count": 0.0, "b": {}})
            if s.name.endswith("_sum"):
                L["sum"] += s.value
            elif s.name.endswith("_count"):
                L["count"] += s.value
            elif s.name.endswith("_bucket"):
                le = s.labels.get("le", "+Inf")
                L["b"][le] = L["b"].get(le, 0.0) + s.value

    duration_s = max(1.0, time.time() - run_start_ts)
    duration_min = duration_s / 60.0
    duration_hr = duration_s / 3600.0

    def is_blocked_or_captcha(labels):
        et = labels.get("error_type", "")
        return et in ("blocked", "captcha")

    # endpoints set
    endpoints = {"overall"}
    for m in REGISTRY.collect():
        if m.name == "scrape_requests_total":
            for s in m.samples:
                endpoints.add(s.labels.get("endpoint", "overall"))

    summary = []
    for ep in sorted(endpoints):
        where_ep = (
            (lambda lab: lab.get("endpoint", "overall") == ep)
            if ep != "overall"
            else (lambda lab: True)
        )

        reqs = sum_counter("scrape_requests_total", where_ep)
        blocked = sum_counter("scrape_errors_total", lambda lab: where_ep(lab) and is_blocked_or_captcha(lab))
        errs_404 = sum_counter("scrape_errors_total", lambda lab: where_ep(lab) and lab.get("error_type") == "404")
        errs_5xx = sum_counter("scrape_errors_total", lambda lab: where_ep(lab) and lab.get("error_type") == "5xx")
        errs_timeout = sum_counter("scrape_errors_total", lambda lab: where_ep(lab) and lab.get("error_type") == "timeout")
        errs_json = sum_counter("scrape_errors_total", lambda lab: where_ep(lab) and lab.get("error_type") == "json_error")
        errs_parse = sum_counter("scrape_errors_total", lambda lab: where_ep(lab) and lab.get("error_type") == "parse_error")

        attempted = sum_counter("scrape_pages_attempted_total", where_ep)
        scraped = sum_counter("scrape_pages_scraped_total", where_ep)
        missing = sum_counter("scrape_missing_field_total", where_ep)
        ipblocks = sum_counter("scrape_ip_blocks_total", lambda lab: True)

        success_pct = (scraped / attempted * 100.0) if attempted > 0 else 0.0
        blocked_pct = (blocked / reqs * 100.0) if reqs > 0 else 0.0
        data_loss_pct = (missing / attempted * 100.0) if attempted > 0 else 0.0
        throughput_m = scraped / duration_min
        throughput_h = scraped / duration_hr

        avg_lat = None
        p95 = None
        if ep in lat and lat[ep]["count"] > 0:
            avg_lat = lat[ep]["sum"] / lat[ep]["count"]
            buckets = list(lat[ep]["b"].items())
            p95 = _quantile_from_buckets(buckets, lat[ep]["count"], 0.95)

        summary.append(
            {
                "endpoint": ep,
                "duration_s": round(duration_s, 3),
                "requests_total": int(reqs),
                "blocked_or_captcha": int(blocked),
                "blocked_pct": round(blocked_pct, 3),
                "errors_404": int(errs_404),
                "errors_5xx": int(errs_5xx),
                "errors_timeout": int(errs_timeout),
                "errors_json": int(errs_json),
                "errors_parse": int(errs_parse),
                "pages_attempted": int(attempted),
                "pages_scraped": int(scraped),
                "success_pct": round(success_pct, 3),
                "data_loss_pct": round(data_loss_pct, 3),
                "throughput_pages_per_min": round(throughput_m, 3),
                "throughput_pages_per_hour": round(throughput_h, 3),
                "latency_avg_sec": None if avg_lat is None else round(avg_lat, 4),
                "latency_p95_sec": None
                if p95 is None or p95 == float("inf")
                else round(p95, 4),
                "ip_blocks": int(ipblocks),
            }
        )

    if summary:
        with open(out_dir / "summary.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
            w.writeheader()
            w.writerows(summary)

    # 4) Per-bucket quick table
    bucket_rows = []
    for m in REGISTRY.collect():
        if m.name != "scrape_pages_scraped_total":
            continue
        for s in m.samples:
            bucket_rows.append(
                {
                    "endpoint": s.labels.get("endpoint", "monthly_archive"),
                    "title": s.labels.get("title", "GM"),
                    "bucket": s.labels.get("bucket", "NA"),
                    "pages_scraped": int(s.value),
                }
            )
    if bucket_rows:
        with open(out_dir / "buckets.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f, fieldnames=["endpoint", "title", "bucket", "pages_scraped"]
            )
            w.writeheader()
            w.writerows(bucket_rows)


# =========================
# Main
# =========================
def main():
    ap = argparse.ArgumentParser(description="Chess.com titled-games collector (Step 1: GM focus)")
    ap.add_argument("--titles", default="GM", help="Comma-separated titles (e.g., GM,IM)")
    ap.add_argument("--limit-users", type=int, default=5, help="Process at most N users per title (smoke test)")
    ap.add_argument("--months-back", type=int, default=1, help="How many recent months to pull per user")
    ap.add_argument("--metrics-port", type=int, default=8000)
    ap.add_argument("--metrics-addr", default="127.0.0.1")
    ap.add_argument("--hold-open", action="store_true", help="Keep metrics server alive after finishing")
    ap.add_argument("--serve-seconds", type=int, default=0, help="If >0, keep server up this many seconds after finishing")
    ap.add_argument("--save-metrics", action="store_true", help="Save metrics snapshots to disk at end of run")
    ap.add_argument("--metrics-dir", default="metrics", help="Directory to write metrics snapshots")
    ap.add_argument("--run-name", default="run", help="Subfolder name under metrics/ for this run")
    args = ap.parse_args()

    start_http_server(args.metrics_port, addr=args.metrics_addr)
    print(f"[metrics] http://{args.metrics_addr}:{args.metrics_port}/metrics")

    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_UA})

    titles = [t.strip().upper() for t in args.titles.split(",") if t.strip()]
    seen = Seen()

    for title in titles:
        # 1) titled list
        t_url = f"{BASE}/titled/{title}"
        t_data = fetch_json("titled_list", t_url, session)
        if not t_data or "players" not in t_data:
            print(f"[warn] no titled players for {title}")
            continue
        users = t_data["players"][: args.limit_users]

        for u in users:
            # 2) archives index
            a_url = f"{BASE}/player/{u}/games/archives"
            a_data = fetch_json("archives_index", a_url, session)
            if not a_data or "archives" not in a_data:
                continue
            months = a_data["archives"][-args.months_back :]

            # 3) monthly archives
            for murl in months:
                data = fetch_json("monthly_archive", murl, session)
                if not data:
                    continue
                try:
                    process_month_games(data, title, seen)
                except Exception:
                    ERRS_TOTAL.labels(SITE, "monthly_archive", "parse_error").inc()
                    continue

    print("[done] Step 1 complete. PGN:", GM_OUT)

    if args.save_metrics:
        save_metrics_snapshot(args.metrics_dir, args.run_name, RUN_START_TS)
        print(f"[metrics] Snapshots saved to {Path(args.metrics_dir) / args.run_name}")

    # keep server alive for dashboards if requested
    if args.hold_open or args.serve_seconds > 0:
        print("[metrics] Holding server open. Press Ctrl+C to exit.")
        try:
            if args.serve_seconds > 0:
                time.sleep(args.serve_seconds)
            else:
                # signal.pause() is not available on Windows; fallback loop
                try:
                    signal.pause()
                except AttributeError:
                    while True:
                        time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
