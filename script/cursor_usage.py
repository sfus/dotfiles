#!/usr/bin/env python3
#
# Inspired by script/claude_usage.py and script/codex_usage.py
#
"""cursor_usage.py — Show local Cursor Agent metrics from state

Cursor stores global state in SQLite (state.vscdb):
  macOS:  ~/Library/Application Support/Cursor/User/globalStorage/state.vscdb
  Linux:  ~/.config/Cursor/User/globalStorage/state.vscdb
  Windows: %APPDATA%\\Cursor\\User\\globalStorage\\state.vscdb

Main data sources:
  - ItemTable: composer.composerHeaders … per-session contextUsagePercent, etc.
  - ItemTable: cursorAuth/stripeMembershipType … plan type (if present)
  - cursorDiskKV: bubbleId:* … per-message tokenCount (may always be 0 on some setups)

Dashboard (Included-Request Usage) integration:
  - From ItemTable cursorAuth/accessToken (JWT) and sub claim, build
    WorkosCursorSessionToken = "<userId>%3A%3A<jwt>",
    then GET https://cursor.com/api/usage?user=<userId>
    (same family as the dashboard usage page; unofficial API, may change)
  - On 401, refresh via refresh_token at api2.cursor.sh/oauth/token and retry

Environment:
  CURSOR_STATE_DB — path to state.vscdb

Commands:
  cursor-usage              one-line summary (default)
  cursor-usage short        same as above
  cursor-usage long         detail (aggregates + session list)
  cursor-usage json         JSON
  cursor-usage --local-only local DB only, no network
  cursor-usage --help

Short line output (single line):
  cursor:#[fg=…]█░░░…#[default] NN% used/limit [~MM-DD hh:mm] (JST)
  Color thresholds match claude_usage (green / yellow / red)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import sqlite3
import ssl
import sys
import calendar
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator
from zoneinfo import ZoneInfo

VERSION = "0.2.0"

CURSOR_OAUTH_CLIENT_ID = "KbZUR41cY7W6zRSdpSUJ7I7mLYBKOCmB"
USAGE_API = "https://cursor.com/api/usage"
OAUTH_TOKEN_URL = "https://api2.cursor.sh/oauth/token"
CURRENT_PERIOD_RPC = (
    "https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
)


def default_state_db_path() -> str:
    env = os.environ.get("CURSOR_STATE_DB")
    if env:
        return os.path.expanduser(env)
    system = platform.system()
    if system == "Darwin":
        return os.path.expanduser(
            "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
        )
    if system == "Linux":
        xdg = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(xdg, "Cursor", "User", "globalStorage", "state.vscdb")
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return os.path.join(appdata, "Cursor", "User", "globalStorage", "state.vscdb")
    return os.path.expanduser("~/.config/Cursor/User/globalStorage/state.vscdb")


def _ssl_ctx() -> ssl.SSLContext:
    return ssl.create_default_context()


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: float = 20.0,
) -> tuple[int, Any]:
    h = dict(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as r:
            raw = r.read()
            if not raw:
                return r.status, None
            return r.status, json.loads(raw.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        try:
            raw = e.read()
            return e.code, json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            return e.code, None


def decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decode JWT payload without signature verification (read-only sub/exp)."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        p = parts[1] + "=" * (4 - len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(p.encode("ascii")))
    except Exception:
        return None


def workos_cookie_value(access_token: str) -> str | None:
    """Build WorkosCursorSessionToken cookie body: userId%3A%3A<jwt>."""
    payload = decode_jwt_payload(access_token)
    if not payload:
        return None
    sub = str(payload.get("sub") or "")
    if "|" in sub:
        user_id = sub.split("|")[-1]
    else:
        user_id = sub
    if not user_id:
        return None
    return f"{user_id}%3A%3A{access_token}"


def refresh_access_token(refresh_token: str) -> str | None:
    body = json.dumps(
        {
            "grant_type": "refresh_token",
            "client_id": CURSOR_OAUTH_CLIENT_ID,
            "refresh_token": refresh_token,
        }
    ).encode()
    st, data = _http_json(
        OAUTH_TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/json"},
        body=body,
    )
    if st != 200 or not isinstance(data, dict):
        return None
    if data.get("shouldLogout"):
        return None
    tok = data.get("access_token")
    return str(tok) if tok else None


@dataclass
class IncludedRequestUsage:
    """Aggregates for Included-Request (REST /api/usage)."""

    used: int
    limit: int | None
    pct: float | None
    start_of_month: datetime | None
    reset_at: datetime | None
    by_model: dict[str, dict[str, Any]]
    plan_total_pct: float | None = None
    error: str | None = None


def fetch_remote_usage(
    access_token: str,
    refresh_token: str | None,
) -> IncludedRequestUsage:
    """Return Included-Request usage from cursor.com API; refresh token on 401."""
    token = access_token
    for attempt in range(2):
        ck = workos_cookie_value(token)
        if not ck:
            return IncludedRequestUsage(
                0, None, None, None, None, {}, error="cannot decode JWT sub"
            )
        user_id = ck.split("%3A%3A")[0]
        headers = {
            "Cookie": f"WorkosCursorSessionToken={ck}",
            "Origin": "https://cursor.com",
            "Accept": "application/json",
            "User-Agent": "cursor_usage.py",
        }
        st, data = _http_json(f"{USAGE_API}?user={urllib.parse.quote(user_id)}", headers=headers)
        if st == 401 and isinstance(token, str) and refresh_token and attempt == 0:
            new_t = refresh_access_token(refresh_token)
            if new_t:
                token = new_t
                continue
        if st != 200 or not isinstance(data, dict):
            err = None
            if isinstance(data, dict):
                err = str(data.get("description") or data.get("error") or "")
            return IncludedRequestUsage(
                0, None, None, None, None, {}, error=err or f"HTTP {st}"
            )
        return _parse_usage_payload(data, token)

    return IncludedRequestUsage(0, None, None, None, None, {}, error="unauthorized")


def _parse_usage_payload(data: dict[str, Any], bearer_for_rpc: str) -> IncludedRequestUsage:
    by_model: dict[str, dict[str, Any]] = {}
    som: datetime | None = None

    raw_som = data.get("startOfMonth")
    if isinstance(raw_som, str):
        som = parse_iso(raw_som)

    for k, v in data.items():
        if k == "startOfMonth" or not isinstance(v, dict):
            continue
        by_model[k] = v

    used_sum = 0
    limit_val: int | None = None
    # Dashboard Included-Request is usually rolled up under the gpt-4 key (legacy name)
    if "gpt-4" in by_model:
        v = by_model["gpt-4"]
        used_sum = int(v.get("numRequests") or 0)
        mx = v.get("maxRequestUsage")
        if isinstance(mx, (int, float)) and mx > 0:
            limit_val = int(mx)
    else:
        for v in by_model.values():
            used_sum += int(v.get("numRequests") or 0)
        limits: list[int] = []
        for v in by_model.values():
            mx = v.get("maxRequestUsage")
            if isinstance(mx, (int, float)) and mx > 0:
                limits.append(int(mx))
        if limits and len(set(limits)) == 1:
            limit_val = limits[0]

    pct: float | None = None
    if limit_val and limit_val > 0:
        pct = min(100.0, 100.0 * used_sum / limit_val)

    reset_at: datetime | None = _next_cycle_reset(som)

    plan_total: float | None = _fetch_plan_total_percent(bearer_for_rpc)

    return IncludedRequestUsage(
        used=used_sum,
        limit=limit_val,
        pct=pct,
        start_of_month=som,
        reset_at=reset_at,
        by_model=by_model,
        plan_total_pct=plan_total,
        error=None,
    )


def _fetch_plan_total_percent(bearer: str) -> float | None:
    """Optional: Connect RPC planUsage.totalPercentUsed (may match dashboard %)."""
    body = json.dumps({}).encode()
    st, data = _http_json(
        CURRENT_PERIOD_RPC,
        method="POST",
        headers={
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
        },
        body=body,
    )
    if st != 200 or not isinstance(data, dict):
        return None
    pu = data.get("planUsage")
    if not isinstance(pu, dict):
        return None
    t = pu.get("totalPercentUsed")
    if isinstance(t, (int, float)) and t == t:  # not NaN
        return float(t)
    return None


def _next_cycle_reset(start_of_month: datetime | None) -> datetime | None:
    """Next billing cycle start (startOfMonth + 1 month, same idea as JS setMonth)."""
    if not start_of_month:
        return None
    y, m = start_of_month.year, start_of_month.month
    if m == 12:
        y, m = y + 1, 1
    else:
        m += 1
    last_day = calendar.monthrange(y, m)[1]
    day = min(start_of_month.day, last_day)
    return start_of_month.replace(year=y, month=m, day=day)


def connect_ro(path: str) -> sqlite3.Connection:
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def item_value(con: sqlite3.Connection, key: str) -> Any | None:
    cur = con.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
    row = cur.fetchone()
    if not row:
        return None
    raw = row[0]
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def iter_bubble_rows(con: sqlite3.Connection) -> Iterator[dict[str, Any]]:
    cur = con.execute(
        "SELECT value FROM cursorDiskKV WHERE key LIKE 'bubbleId:%'"
    )
    for (raw,) in cur:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(d, dict):
            yield d


def aggregate_bubbles(
    con: sqlite3.Connection,
    since: datetime | None,
) -> dict[str, Any]:
    """Sum tokenCount and count bubbles since ``since`` (UTC)."""
    tot = {"input": 0, "output": 0, "bubbles": 0, "user_bubbles": 0, "assistant_bubbles": 0}
    for b in iter_bubble_rows(con):
        created = parse_iso(b.get("createdAt"))
        if since is not None:
            if created is None or created < since:
                continue
        tot["bubbles"] += 1
        t = b.get("type")
        if t == 1:
            tot["user_bubbles"] += 1
        elif t == 2:
            tot["assistant_bubbles"] += 1
        tc = b.get("tokenCount") or {}
        tot["input"] += int(tc.get("inputTokens") or 0)
        tot["output"] += int(tc.get("outputTokens") or 0)
    return tot


def composer_headers(con: sqlite3.Connection) -> dict[str, Any] | None:
    data = item_value(con, "composer.composerHeaders")
    return data if isinstance(data, dict) else None


def membership_type(con: sqlite3.Connection) -> str | None:
    raw = item_value(con, "cursorAuth/stripeMembershipType")
    if isinstance(raw, str):
        return raw
    return None


def _str_token(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, bytes):
        val = val.decode("utf-8", errors="replace")
    if not isinstance(val, str):
        return None
    s = val.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        try:
            return str(json.loads(s))
        except json.JSONDecodeError:
            pass
    return s or None


def load_auth_tokens(con: sqlite3.Connection) -> tuple[str | None, str | None]:
    return _str_token(item_value(con, "cursorAuth/accessToken")), _str_token(
        item_value(con, "cursorAuth/refreshToken")
    )


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _fmt_reset_short(dt: datetime | None) -> str:
    if not dt:
        return "--"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    jst = dt.astimezone(ZoneInfo("Asia/Tokyo"))
    return f"[~{jst.strftime('%m-%d %H:%M')}]"


def pct_bar(v: float, width: int = 10) -> str:
    """Block progress bar (0..1), same as claude_usage."""
    filled = round(max(0.0, min(1.0, v)) * width)
    return "█" * filled + "░" * (width - filled)


def tmux_color(v: float) -> str:
    """tmux #[fg=…] by utilization ratio (same thresholds as claude_usage / statusline).

    green  < 70 %
    yellow  70–89 %
    red    >= 90 %
    """
    if v >= 0.90:
        return "#[fg=red]"
    if v >= 0.70:
        return "#[fg=yellow]"
    return "#[fg=green]"


def fmt_pct(v: float) -> str:
    """Format ratio 0..1 as percent string (same as claude_usage)."""
    return f"{v * 100:.0f}%"


def _included_util_ratio(remote: IncludedRequestUsage) -> float | None:
    """Utilization 0..1; plan_total_pct / pct are passed as 0..100."""
    p = remote.plan_total_pct if remote.plan_total_pct is not None else remote.pct
    if p is None:
        return None
    return max(0.0, min(1.0, float(p) / 100.0))


def _fmt_short_line(remote: IncludedRequestUsage | None) -> str:
    """One tmux line: cursor: + colored bar + % + used/limit + [~MM-DD hh:mm] JST."""
    if not remote:
        return "cursor:#[fg=colour245]--#[default]"
    if remote.error:
        return f"cursor:#[fg=red]{remote.error}#[default]"
    ratio = _included_util_ratio(remote)
    if ratio is None:
        parts = ["cursor:"]
        if remote.limit:
            parts.append(f"{remote.used}/{remote.limit}")
        else:
            parts.append(f"used:{remote.used}")
        parts.append(_fmt_reset_short(remote.reset_at))
        return " ".join(parts)

    c = tmux_color(ratio)
    bar = f"{c}{pct_bar(ratio)}#[default]"
    used_lim = (
        f"{remote.used}/{remote.limit}" if remote.limit else f"used:{remote.used}"
    )
    return (
        f"cursor:{bar} {fmt_pct(ratio)} {used_lim} "
        f"{_fmt_reset_short(remote.reset_at)}"
    )


def fmt_short(
    _membership: str | None,
    _agg_5h: dict[str, Any],
    _agg_day: dict[str, Any],
    _agg_7d: dict[str, Any],
    _headers: dict[str, Any] | None,
    remote: IncludedRequestUsage | None,
) -> str:
    return _fmt_short_line(remote)


def _max_context_percent(headers: dict[str, Any] | None) -> float | None:
    if not headers:
        return None
    composers = headers.get("allComposers")
    if not isinstance(composers, list):
        return None
    best: float | None = None
    for c in composers:
        if not isinstance(c, dict):
            continue
        v = c.get("contextUsagePercent")
        if isinstance(v, (int, float)):
            best = float(v) if best is None else max(best, float(v))
    return best


def build_long(
    db_path: str,
    membership: str | None,
    agg_5h: dict[str, Any],
    agg_day: dict[str, Any],
    agg_7d: dict[str, Any],
    headers: dict[str, Any] | None,
    remote: IncludedRequestUsage | None,
) -> str:
    lines = [
        f"state_db: {db_path}",
        f"membership: {membership or '(unknown)'}",
        "",
        "--- Included-Request (cursor.com/api/usage) ---",
    ]
    if remote:
        if remote.error:
            lines.append(f"  error: {remote.error}")
        else:
            ru = _included_util_ratio(remote)
            if ru is not None:
                lines.append(
                    f"  util: {fmt_pct(ru)} [{pct_bar(ru, width=20)}]"
                )
            pct_disp = remote.plan_total_pct if remote.plan_total_pct is not None else remote.pct
            lines.append(
                f"  used/limit: {remote.used}"
                + (f" / {remote.limit}" if remote.limit else "")
                + (
                    f"  ({pct_disp:.1f}%)" if pct_disp is not None else ""
                )
            )
            lines.append(
                f"  cycle start: {remote.start_of_month.isoformat() if remote.start_of_month else '-'}"
            )
            lines.append(
                f"  next reset:  {remote.reset_at.isoformat() if remote.reset_at else '-'}"
            )
            if remote.plan_total_pct is not None and remote.pct is not None:
                lines.append(
                    f"  note: planUsage.totalPercentUsed={remote.plan_total_pct:.2f}% "
                    f"(REST request ratio {remote.pct:.2f}%)"
                )
            for mk, mv in sorted(remote.by_model.items()):
                lines.append(
                    f"    {mk}: requests {mv.get('numRequests')}"
                    f" / {mv.get('maxRequestUsage')}  tokens {mv.get('numTokens')}"
                )
    else:
        lines.append("  (skipped)")
    lines.extend([
        "",
        "--- Token aggregates (bubble tokenCount; may be 0 if not stored) ---",
        f"  5h : in {fmt_tokens(agg_5h['input']):>8}  out {fmt_tokens(agg_5h['output']):>8}  "
        f"bubbles {agg_5h['bubbles']}",
        f"  day: in {fmt_tokens(agg_day['input']):>8}  out {fmt_tokens(agg_day['output']):>8}  "
        f"bubbles {agg_day['bubbles']}",
        f"  7d : in {fmt_tokens(agg_7d['input']):>8}  out {fmt_tokens(agg_7d['output']):>8}  "
        f"bubbles {agg_7d['bubbles']}",
        "",
        "--- Agent / Composer sessions (from composer.composerHeaders) ---",
    ])
    if not headers or not isinstance(headers.get("allComposers"), list):
        lines.append("  (no composer.composerHeaders data)")
    else:
        rows: list[tuple[float, str]] = []
        for c in headers["allComposers"]:
            if not isinstance(c, dict):
                continue
            if c.get("isDraft"):
                continue
            name = str(c.get("name") or "(untitled)")
            mode = str(c.get("unifiedMode") or "")
            ctx = c.get("contextUsagePercent")
            ctx_s = f"{float(ctx):.1f}%" if isinstance(ctx, (int, float)) else "-"
            lu = c.get("lastUpdatedAt")
            ts_s = "-"
            if isinstance(lu, (int, float)):
                dt = datetime.fromtimestamp(lu / 1000.0, tz=timezone.utc)
                ts_s = dt.strftime("%Y-%m-%d %H:%M UTC")
            line = f"{name[:40]:<40} mode:{mode:<8} ctx:{ctx_s:<7} upd:{ts_s}"
            key = float(ctx) if isinstance(ctx, (int, float)) else -1.0
            rows.append((key, f"  {line}"))
        rows.sort(key=lambda x: x[0], reverse=True)
        if rows:
            lines.extend(r[1] for r in rows[:24])
            if len(rows) > 24:
                lines.append(f"  ... ({len(rows) - 24} more)")
        else:
            lines.append("  (no non-draft composers)")
    return "\n".join(lines)


def _serialize_remote(r: IncludedRequestUsage) -> dict[str, Any]:
    return {
        "used": r.used,
        "limit": r.limit,
        "pct": r.pct,
        "plan_total_pct": r.plan_total_pct,
        "start_of_month": r.start_of_month.isoformat() if r.start_of_month else None,
        "reset_at": r.reset_at.isoformat() if r.reset_at else None,
        "by_model": r.by_model,
        "error": r.error,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show Cursor Agent usage metrics from local state.vscdb.",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("short", "long", "json"),
        default="short",
        help="output mode (default: short)",
    )
    parser.add_argument(
        "--db",
        metavar="PATH",
        help="override path to state.vscdb (default: env CURSOR_STATE_DB or OS default)",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="do not call cursor.com / api2.cursor.sh (offline)",
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")
    args = parser.parse_args()

    if args.version:
        print(f"cursor-usage {VERSION}")
        return 0

    db_path = os.path.expanduser(args.db) if args.db else default_state_db_path()
    if not os.path.isfile(db_path):
        print(f"[--] state.vscdb not found: {db_path}", file=sys.stderr)
        return 1

    try:
        con = connect_ro(db_path)
    except sqlite3.Error as e:
        print(f"[--] cannot open database: {e}", file=sys.stderr)
        return 1

    try:
        now = datetime.now(timezone.utc)
        day_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
        agg_5h = aggregate_bubbles(con, now - timedelta(hours=5))
        agg_day = aggregate_bubbles(con, day_start)
        agg_7d = aggregate_bubbles(con, now - timedelta(days=7))
        headers = composer_headers(con)
        membership = membership_type(con)
        access_tok, refresh_tok = load_auth_tokens(con)
    finally:
        con.close()

    remote: IncludedRequestUsage | None = None
    if not args.local_only and access_tok:
        remote = fetch_remote_usage(access_tok, refresh_tok)
    elif not args.local_only and not access_tok:
        remote = IncludedRequestUsage(
            0, None, None, None, None, {}, error="no cursorAuth/accessToken in state.vscdb"
        )

    if args.mode == "json":
        out: dict[str, Any] = {
            "version": VERSION,
            "state_db": db_path,
            "membership": membership,
            "included_request": _serialize_remote(remote) if remote else None,
            "aggregates": {
                "5h": agg_5h,
                "today_utc": agg_day,
                "7d": agg_7d,
            },
            "composer_headers": headers,
            "generated_at": now.isoformat(),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.mode == "long":
        print(
            build_long(
                db_path,
                membership,
                agg_5h,
                agg_day,
                agg_7d,
                headers,
                remote,
            )
        )
        return 0

    # short
    print(
        fmt_short(
            membership,
            agg_5h,
            agg_day,
            agg_7d,
            headers,
            remote,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
