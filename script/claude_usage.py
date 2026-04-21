#!/usr/bin/env python3
#
# Original: https://github.com/long-910/tmux-claude-status
# (MIT License)
# Doc: https://zenn.dev/long910/articles/2026-02-23-claude-tmux-status

"""claude_usage.py - Claude Code usage for tmux status bar

Default mode (no API calls):
  Reads cached rate-limit data. Updates cache only when Claude Code
  JSONL files change (i.e., when Claude is actually being used).
  Shows staleness indicator when data is not fresh.

Realtime mode (opt-in, costs tokens):
  Polls Anthropic API every 5 min regardless of Claude activity.
  Cost: ~$0.001/day, ~$0.009/week, ~$0.04/month.

Provider auto-detection:
  anthropic  OAuth credentials found → rate-limit % display (default)
  other      No OAuth (Bedrock / API key) → cost display from JSONL

Commands:
  claude-usage              short display (current mode)
  claude-usage short        compact for tmux
  claude-usage long         full breakdown (percent + cost)
  claude-usage json         JSON output
  claude-usage cost         force cost display
  claude-usage toggle       switch percent / cost display
  claude-usage dashboard    interactive full-screen dashboard (tmux popup)
  claude-usage --version    show version and exit
  claude-usage --help       show help and exit
  claude-usage --refresh    force API update (for hooks / manual)
  claude-usage --install-hook  add Stop hook to ~/.claude/settings.json

Settings: ~/.claude/tmux-claude-status.json
  {
    "realtime": false,
    "cache_ttl": 300,
    "provider": "auto"    // "auto" | "anthropic" | "bedrock" | "other"
  }
"""

import json
import os
import glob
import platform
import ssl
import subprocess
import sys
import time
import urllib.request
import re
import urllib.error
from datetime import datetime, date, timedelta, timezone

CREDENTIALS_FILE = os.path.expanduser("~/.claude/.credentials.json")
SETTINGS_FILE    = os.path.expanduser("~/.claude/tmux-claude-status.json")
MODE_FILE        = os.path.expanduser("~/.claude/tmux-display-mode")
CACHE_FILE       = os.path.expanduser("~/.claude/tmux-rate-limit-cache.json")
CLAUDE_PROJECTS  = os.path.expanduser("~/.claude/projects")
CLAUDE_SETTINGS  = os.path.expanduser("~/.claude/settings.json")

DEFAULT_SETTINGS = {
    "realtime": False,
    "cache_ttl": 300,
    "provider": "auto",
    # Claude Code stores credentials as JSON in the OS keychain under this service name.
    # The account defaults to the OS login name (same as Claude Code's behavior).
    "keychain_service": "Claude Code-credentials",
    "keychain_account": os.getenv("USER", os.getenv("LOGNAME", "")),
}

PRICING = {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_create": 3.75}

DASH_WIDTH = 78  # inner width between '+' delimiters (total box = 80 cols)
VERSION    = "0.8.0"


# -- Settings -----------------------------------------------------------------

def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    except Exception:
        return dict(DEFAULT_SETTINGS)


def _keychain_json(service, account):
    """Read and parse a JSON secret from the OS keychain.

    Claude Code stores credentials as a JSON blob (not a raw token string), so
    this helper returns the parsed dict rather than the raw string.

    macOS  – delegates to the built-in `security` CLI (no extra deps).
    Linux  – delegates to `secret-tool` (libsecret); returns None if absent.
    Other  – not supported; returns None.
    """
    system = platform.system()
    raw = None
    try:
        if system == "Darwin":
            result = subprocess.run(
                ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                raw = result.stdout.strip()
        elif system == "Linux":
            result = subprocess.run(
                ["secret-tool", "lookup", "service", service, "account", account],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                raw = result.stdout.strip()
    except Exception:
        return None

    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def get_access_token(settings=None):
    """Return the Claude OAuth access token.

    Resolution order:
      1. OS keychain  – Claude Code stores a JSON blob under service
                        "Claude Code-credentials" / account = OS username.
      2. ~/.claude/.credentials.json  – legacy / non-keychain fallback.

    Keychain keys (override in tmux-claude-status.json if needed):
      keychain_service  – default: "Claude Code-credentials"
      keychain_account  – default: current OS login name
    """
    if settings is None:
        settings = load_settings()

    service = settings.get("keychain_service", DEFAULT_SETTINGS["keychain_service"])
    account = settings.get("keychain_account", DEFAULT_SETTINGS["keychain_account"])

    creds = _keychain_json(service, account)
    if creds:
        token = creds.get("claudeAiOauth", {}).get("accessToken")
        if token:
            return token

    # Fall back to the JSON credentials file
    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)["claudeAiOauth"]["accessToken"]
    except Exception:
        return None


def detect_provider(settings):
    """Detect the Claude provider.

    Returns "anthropic" if OAuth credentials exist (Claude.ai subscription),
    otherwise "other" (AWS Bedrock, raw API key, etc.).

    Override with settings["provider"]: "auto" | "anthropic" | "bedrock" | "other"
    Any value other than "auto" and "anthropic" is treated as non-subscription.
    """
    override = settings.get("provider", "auto")
    if override != "auto":
        return "anthropic" if override == "anthropic" else "other"

    if get_access_token(settings):
        return "anthropic"
    return "other"


# -- Display mode (percent / cost) --------------------------------------------

def get_display_mode():
    try:
        return open(MODE_FILE).read().strip()
    except Exception:
        return "percent"


def toggle_display_mode():
    new = "cost" if get_display_mode() == "percent" else "percent"
    with open(MODE_FILE, "w") as f:
        f.write(new)
    return new


# -- JSONL latest mtime -------------------------------------------------------

def latest_jsonl_mtime():
    mt = 0.0
    if not os.path.isdir(CLAUDE_PROJECTS):
        return mt
    for path in glob.glob(f"{CLAUDE_PROJECTS}/**/*.jsonl", recursive=True):
        try:
            mt = max(mt, os.path.getmtime(path))
        except Exception:
            pass
    return mt


# -- Cache --------------------------------------------------------------------

def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(data):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


# -- Anthropic API call -------------------------------------------------------

def fetch_rate_limit():
    """One minimal API call (claude-haiku, 1 output token) to get rate-limit headers.
    Cost: ~$0.0000046 per call (8 input + 1 output tokens at Haiku pricing).
    """
    token = get_access_token()
    if not token:
        return None

    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "."}],
    }).encode()
    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body, headers=headers, method="POST",
        )
        _ctx = ssl.create_default_context()
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            _ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        with urllib.request.urlopen(req, timeout=10, context=_ctx) as r:
            rl = {k.lower(): v for k, v in r.headers.items()
                  if "ratelimit-unified" in k.lower()}
            return {
                "fetched_at": time.time(),
                "util_5h":    float(rl.get("anthropic-ratelimit-unified-5h-utilization", 0)),
                "util_7d":    float(rl.get("anthropic-ratelimit-unified-7d-utilization", 0)),
                "reset_5h":   int(rl.get("anthropic-ratelimit-unified-5h-reset", 0)),
                "reset_7d":   int(rl.get("anthropic-ratelimit-unified-7d-reset", 0)),
                "status_5h":  rl.get("anthropic-ratelimit-unified-5h-status", ""),
                "status_7d":  rl.get("anthropic-ratelimit-unified-7d-status", ""),
                "overall":    rl.get("anthropic-ratelimit-unified-status", ""),
            }
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode()[:200]
        except Exception:
            pass
        return {"_error": f"HTTP {e.code} {e.reason}", "_body": err_body}
    except urllib.error.URLError as e:
        return {"_error": f"URL error: {e.reason}"}
    except Exception as e:
        return {"_error": str(e)}


def get_rate_limit(force=False):
    """Return rate-limit data from cache or API depending on settings.

    Default mode (realtime=False):
      API is called ONLY when both conditions are true:
        1. Cache is older than cache_ttl
        2. JSONL files were updated after the last cache write
           (= Claude was actually used since last update)

    Realtime mode (realtime=True):
      API is called whenever cache is older than cache_ttl,
      regardless of Claude activity. Costs ~$0.001/day.
    """
    settings = load_settings()
    ttl      = settings.get("cache_ttl", 300)
    realtime = settings.get("realtime", False)
    cache    = load_cache()
    now      = time.time()
    cache_age = (now - cache["fetched_at"]) if cache else float("inf")

    if force:
        data = fetch_rate_limit()
        if data and "_error" not in data:
            save_cache(data)
        return data or cache

    if cache and cache_age < ttl:
        return cache  # Cache is fresh; never hit the API

    if realtime:
        # Realtime mode: refresh on TTL expiry regardless of Claude activity
        data = fetch_rate_limit()
        if data and "_error" not in data:
            save_cache(data)
            return data
        return cache

    # Default mode: only refresh if Claude was RECENTLY active (within ttl window).
    # "Recently active" = JSONL files were updated within the last ttl seconds.
    # This ensures we never call the API when Claude is idle, even if cache is stale.
    jmtime = latest_jsonl_mtime()
    recently_active = jmtime > 0 and (now - jmtime) < ttl

    if recently_active:
        data = fetch_rate_limit()
        if data:
            save_cache(data)
            return data

    return cache  # Claude idle or API failed → return stale cache (may be None)


# -- Claude Code hook install -------------------------------------------------

def install_hook():
    """Add a Stop hook to ~/.claude/settings.json so the cache is updated
    whenever a Claude Code session ends (zero extra token cost for the hook
    itself; the hook triggers one --refresh API call per session end)."""
    refresh_cmd = (
        os.path.expanduser("~/.local/bin/claude-usage")
        + " --refresh >/dev/null 2>&1"
    )
    try:
        with open(CLAUDE_SETTINGS) as f:
            settings = json.load(f)
    except Exception:
        settings = {}

    hooks     = settings.setdefault("hooks", {})
    stop_list = hooks.setdefault("Stop", [])

    for entry in stop_list:
        for h in entry.get("hooks", []):
            if "claude-usage" in h.get("command", ""):
                print("[skip] Stop hook already configured")
                return

    stop_list.append({"hooks": [{"type": "command", "command": refresh_cmd}]})

    with open(CLAUDE_SETTINGS, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print("[ok] Stop hook added to ~/.claude/settings.json")
    print("     Cache will update automatically at end of each Claude session.")


def uninstall_hook():
    """Remove the claude-usage Stop hook from ~/.claude/settings.json."""
    try:
        with open(CLAUDE_SETTINGS) as f:
            settings = json.load(f)
    except Exception:
        print("[skip] ~/.claude/settings.json not found or invalid")
        return

    hooks = settings.get("hooks", {})
    stop_list = hooks.get("Stop", [])
    new_stop = [
        entry for entry in stop_list
        if not any("claude-usage" in h.get("command", "")
                   for h in entry.get("hooks", []))
    ]

    if len(new_stop) == len(stop_list):
        print("[skip] No claude-usage Stop hook found")
        return

    hooks["Stop"] = new_stop
    if not hooks["Stop"]:
        del hooks["Stop"]
    if not hooks:
        del settings["hooks"]

    with open(CLAUDE_SETTINGS, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print("[ok] Stop hook removed from ~/.claude/settings.json")


# -- Cost aggregation from local JSONL ----------------------------------------

def load_jsonl_records():
    records = []
    if not os.path.isdir(CLAUDE_PROJECTS):
        return records
    for path in glob.glob(f"{CLAUDE_PROJECTS}/**/*.jsonl", recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    msg = data.get("message", {})
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {})
                    if not usage:
                        continue
                    ts = data.get("timestamp")
                    if not ts:
                        continue
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        records.append((dt, usage))
                    except Exception:
                        continue
        except Exception:
            continue
    return records


def decode_project_name(folder_name):
    """Convert Claude Code's encoded project folder name to a human-readable label.

    Claude Code stores projects as absolute paths with '/' → '-', e.g.:
      /home/user/my-project  →  -home-user-my-project
    """
    name = folder_name.lstrip('-')
    parts = name.split('-')
    # Strip common 'home-<user>-' prefix so only the project portion remains
    if len(parts) >= 3 and parts[0] == 'home':
        name = '-'.join(parts[2:])
    return name or folder_name


def load_jsonl_records_by_project():
    """Like load_jsonl_records() but groups records by decoded project name.

    Returns dict: project_name -> list of (datetime, usage_dict)
    """
    projects = {}
    if not os.path.isdir(CLAUDE_PROJECTS):
        return projects
    for path in glob.glob(f"{CLAUDE_PROJECTS}/**/*.jsonl", recursive=True):
        folder = os.path.basename(os.path.dirname(path))
        proj_name = decode_project_name(folder)
        proj_list = projects.setdefault(proj_name, [])
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    msg = data.get("message", {})
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {})
                    if not usage:
                        continue
                    ts = data.get("timestamp")
                    if not ts:
                        continue
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        proj_list.append((dt, usage))
                    except Exception:
                        continue
        except Exception:
            continue
    return projects


def aggregate(records, since):
    t = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "records": 0}
    for dt, usage in records:
        if dt >= since:
            t["input"]        += usage.get("input_tokens", 0)
            t["output"]       += usage.get("output_tokens", 0)
            t["cache_read"]   += usage.get("cache_read_input_tokens", 0)
            t["cache_create"] += usage.get("cache_creation_input_tokens", 0)
            t["records"]      += 1
    return t


def calc_cost(t):
    return (
        t["input"]        * PRICING["input"]
        + t["output"]     * PRICING["output"]
        + t["cache_read"] * PRICING["cache_read"]
        + t["cache_create"] * PRICING["cache_create"]
    ) / 1_000_000


# -- Formatters ---------------------------------------------------------------

def fmt_tokens(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)


def fmt_cost(c):
    if c >= 100: return f"${c:.1f}"
    if c >= 10:  return f"${c:.2f}"
    return f"${c:.3f}"


def fmt_pct(v):
    return f"{v*100:.0f}%"


def fmt_reset(ts):
    secs = int(max(0, ts - time.time()))
    if secs < 86400:
        h, m = divmod(secs // 60, 60)
        return f"{h}h{m:02d}m"
    d = secs // 86400
    h = (secs % 86400) // 3600
    if h:
        return f"{d}d{h}h"
    return f"{d}d"


def fmt_age(fetched_at):
    """Return staleness label; empty string if data is fresh (< 2 min)."""
    if not fetched_at:
        return " [--]"
    age = time.time() - fetched_at
    if age < 120:   return ""
    if age < 3600:  return f" [{int(age/60)}m ago]"
    if age < 86400: return f" [{int(age/3600)}h ago]"
    return f" [{int(age/86400)}d ago]"


def pct_bar(v, width=10):
    """Block-character progress bar (e.g. '███░░░░░░░')."""
    filled = round(max(0.0, min(1.0, v)) * width)
    return "█" * filled + "░" * (width - filled)


def tmux_color(v):
    """Return tmux #[fg=…] directive based on utilization ratio.

    Matches the statusline.sh colour thresholds:
      green  < 70 %
      yellow  70–89 %
      red    >= 90 %
    """
    if v >= 0.90: return "#[fg=red]"
    if v >= 0.70: return "#[fg=yellow]"
    return "#[fg=green]"


def status_ind(status):
    if status in ("denied", "blocked"): return "X"
    if "warning" in status:             return "!"
    return ""


def progress_bar(ratio, width=20, fill='█', empty='░'):
    """Render a fixed-width block progress bar."""
    ratio = max(0.0, min(1.0, ratio))
    filled = round(ratio * width)
    return f"{fill * filled}{empty * (width - filled)}"


# -- Output formatters --------------------------------------------------------

def has_7d_limit(rl):
    """Return True if the rate limit data includes a weekly (7d) limit."""
    return rl.get("reset_7d", 0) > 0 or rl.get("util_7d", 0) > 0


def short_percent(rl):
    u5   = rl["util_5h"]
    age  = fmt_age(rl.get("fetched_at", 0))
    ind5 = status_ind(rl["status_5h"])
    r5   = fmt_reset(rl["reset_5h"])
    bar5 = f"{tmux_color(u5)}{pct_bar(u5)}#[default]"
    if has_7d_limit(rl):
        u7   = rl["util_7d"]
        ind7 = status_ind(rl["status_7d"])
        r7   = fmt_reset(rl["reset_7d"])
        bar7 = f"{tmux_color(u7)}{pct_bar(u7)}#[default]"
        return (
            f"5h:{bar5} {fmt_pct(u5)}{ind5}({r5}) "
            f"7d:{bar7} {fmt_pct(u7)}{ind7}({r7})"
            f"{age}"
        )
    # 5h-only plan (no weekly limit)
    return f"5h:{bar5} {fmt_pct(u5)}{ind5}({r5}){age}"


def short_cost(records):
    now  = datetime.now(timezone.utc)
    t5h  = aggregate(records, now - timedelta(hours=5))
    tday = aggregate(records, datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc))
    t7d  = aggregate(records, now - timedelta(days=7))
    return (
        f"5h:{fmt_cost(calc_cost(t5h))} "
        f"day:{fmt_cost(calc_cost(tday))} "
        f"7d:{fmt_cost(calc_cost(t7d))}"
    )


def long_output(rl, records, settings):
    lines = []
    realtime = settings.get("realtime", False)
    provider = detect_provider(settings)
    mode_lbl = "realtime(5min)" if realtime else "default(no API)"
    prov_lbl = settings.get("provider", "auto")

    lines.append(f"-- Rate Limit [{mode_lbl}] provider:{prov_lbl}({provider}) " + "-" * 18)
    if provider == "other":
        lines.append("  [not available] AWS Bedrock / API key — showing cost from local JSONL")
    elif rl:
        u5  = rl["util_5h"]
        age = fmt_age(rl.get("fetched_at", 0)).strip()
        lines.append(f"  5h: {fmt_pct(u5):>4} [{pct_bar(u5)}] reset:{fmt_reset(rl['reset_5h'])}  ({rl['status_5h']})")
        if has_7d_limit(rl):
            u7 = rl["util_7d"]
            lines.append(f"  7d: {fmt_pct(u7):>4} [{pct_bar(u7)}] reset:{fmt_reset(rl['reset_7d'])}  ({rl['status_7d']})")
        else:
            lines.append("  7d: [no weekly limit on this plan]")
        lines.append(f"  last updated: {age or 'just now'}")
    else:
        lines.append("  [no data] run: claude-usage --refresh")

    now = datetime.now(timezone.utc)
    def row(label, t):
        return (
            f"  {label}: in:{fmt_tokens(t['input'])} out:{fmt_tokens(t['output'])} "
            f"cr:{fmt_tokens(t['cache_read'])} cw:{fmt_tokens(t['cache_create'])} "
            f"cost:{fmt_cost(calc_cost(t))}"
        )
    lines.append("-- Token Cost [local JSONL] " + "-" * 33)
    lines.append(row("5h ", aggregate(records, now - timedelta(hours=5))))
    lines.append(row("day", aggregate(records, datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc))))
    lines.append(row("7d ", aggregate(records, now - timedelta(days=7))))
    return "\n".join(lines)


# -- Dashboard ----------------------------------------------------------------

def _dline(char='-'):
    """Full-width horizontal divider for the dashboard box."""
    return '+' + char * DASH_WIDTH + '+'


def _drow(content=''):
    """Left-aligned row inside the dashboard box."""
    content = str(content)
    inner = DASH_WIDTH - 2
    if len(content) > inner:
        content = content[:inner - 3] + '...'
    return '| ' + content + ' ' * (inner - len(content)) + ' |'


def _drow2(left, right):
    """Row with left- and right-aligned text inside the dashboard box."""
    inner = DASH_WIDTH - 2
    left, right = str(left), str(right)
    if len(left) + 1 + len(right) > inner:
        left = left[:inner - len(right) - 4] + '...'
    pad = inner - len(left) - len(right)
    return '| ' + left + ' ' * max(1, pad) + right + ' |'


def render_dashboard(rl, records, proj_records, settings):
    """Render the full dashboard as a multi-line string."""
    now = datetime.now(timezone.utc)
    provider = detect_provider(settings)
    realtime = settings.get("realtime", False)
    prov_setting = settings.get("provider", "auto")
    mode_lbl = "realtime" if realtime else "default(no API)"

    L = []

    # ── Header ───────────────────────────────────────────────────────────
    L.append(_dline('='))
    title = 'Claude Usage Dashboard'
    pad = (DASH_WIDTH - 2 - len(title)) // 2
    L.append(_drow(' ' * pad + title))
    L.append(_dline('='))

    # ── Rate Limits ──────────────────────────────────────────────────────
    if provider == "anthropic":
        age_raw = fmt_age(rl.get("fetched_at", 0)) if rl else " [--]"
        age_label = age_raw.strip() or '[just now]'
        L.append(_drow2("  Rate Limits", age_label))
        L.append(_drow())
        if rl:
            u5 = rl["util_5h"]
            s5 = status_ind(rl["status_5h"])
            L.append(_drow(
                f"  5h: {fmt_pct(u5):>4}{s5}  {progress_bar(u5)}"
                f"  reset {fmt_reset(rl['reset_5h']):<10}  ({rl['status_5h']})"
            ))
            if has_7d_limit(rl):
                u7 = rl["util_7d"]
                s7 = status_ind(rl["status_7d"])
                L.append(_drow(
                    f"  7d: {fmt_pct(u7):>4}{s7}  {progress_bar(u7)}"
                    f"  reset {fmt_reset(rl['reset_7d']):<10}  ({rl['status_7d']})"
                ))
            else:
                L.append(_drow("  7d: [no weekly limit on this plan]"))
        else:
            L.append(_drow("  [no data]  run: claude-usage --refresh"))
    else:
        L.append(_drow("  Rate Limits: [not available]  AWS Bedrock / API key user"))

    L.append(_drow())
    L.append(_dline())

    # ── Token Usage & Cost ───────────────────────────────────────────────
    L.append(_drow("  Token Usage & Cost"))
    L.append(_drow())
    L.append(_drow(
        f"  {'':6}  {'Input':>9}  {'Output':>9}  {'CacheRd':>9}  {'CacheWr':>9}  {'Cost':>9}"
    ))

    def _cost_row(label, since):
        t = aggregate(records, since)
        return (
            f"  {label:>6}  {fmt_tokens(t['input']):>9}  {fmt_tokens(t['output']):>9}  "
            f"{fmt_tokens(t['cache_read']):>9}  {fmt_tokens(t['cache_create']):>9}  "
            f"{fmt_cost(calc_cost(t)):>9}"
        )

    L.append(_drow(_cost_row("5h", now - timedelta(hours=5))))
    L.append(_drow(_cost_row(
        "Today",
        datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc),
    )))
    L.append(_drow(_cost_row("7d", now - timedelta(days=7))))
    L.append(_drow())
    L.append(_dline())

    # ── Top Projects (7-day cost) ─────────────────────────────────────────
    L.append(_drow("  Top Projects  (7-day cost)"))
    L.append(_drow())

    since_7d = now - timedelta(days=7)
    proj_costs = [
        (name, calc_cost(aggregate(recs, since_7d)))
        for name, recs in proj_records.items()
    ]
    proj_costs = [(n, c) for n, c in proj_costs if c > 0]
    proj_costs.sort(key=lambda x: x[1], reverse=True)

    if proj_costs:
        total_7d = sum(c for _, c in proj_costs)
        for pname, c in proj_costs[:8]:
            ratio = c / total_7d if total_7d > 0 else 0.0
            pct_str = f"{ratio * 100:.0f}%"
            bar_str = progress_bar(ratio, width=18)
            name_max = 22
            display = (pname[:name_max - 1] + '>') if len(pname) > name_max else pname
            L.append(_drow(
                f"  {display:<{name_max}}  {fmt_cost(c):>8}  {bar_str}  {pct_str}"
            ))
    else:
        L.append(_drow("  [no project data found]"))

    L.append(_drow())
    L.append(_dline())

    # ── Status bar ────────────────────────────────────────────────────────
    L.append(_drow(
        f"  Provider: {provider}({prov_setting})"
        f"  |  Mode: {mode_lbl}"
        f"  |  Display: {get_display_mode()}"
    ))
    L.append(_drow2("", f"v{VERSION}  "))
    L.append(_dline('='))
    L.append("")
    L.append("  [r] refresh    [w] toggle watch(30s)    [q] quit")

    return "\n".join(L)


def read_key(timeout=None):
    """Read a single keypress from stdin. Returns None on timeout or non-TTY."""
    if not sys.stdin.isatty():
        return None
    try:
        import tty
        import termios
        import select as _select
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            if timeout is not None:
                ready, _, _ = _select.select([sys.stdin], [], [], timeout)
                if not ready:
                    return None
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        return None


def dashboard_cmd():
    """Interactive full-screen dashboard, designed for use in a tmux popup."""
    import signal

    settings = load_settings()
    provider = detect_provider(settings)
    watch = False
    interactive = sys.stdin.isatty()

    def fetch():
        rl = get_rate_limit() if provider == "anthropic" else None
        return rl, load_jsonl_records(), load_jsonl_records_by_project()

    rl, records, proj_records = fetch()

    # Non-interactive: just print and exit (e.g. piped or testing)
    if not interactive:
        print(render_dashboard(rl, records, proj_records, settings))
        return

    def handle_sigint(sig, frame):
        sys.stdout.write("\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    while True:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        print(render_dashboard(rl, records, proj_records, settings))

        key = read_key(timeout=30 if watch else 120)

        if key in ('q', 'Q', '\x03', '\x1b'):   # q / Ctrl-C / Esc
            break
        elif key in ('r', 'R'):
            rl, records, proj_records = fetch()
        elif key in ('w', 'W'):
            watch = not watch
            if watch:
                rl, records, proj_records = fetch()
        elif key is None and watch:
            rl, records, proj_records = fetch()
        # Non-watch 120s timeout: redraw without API call (falls through to top)


# -- Main ---------------------------------------------------------------------

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "short"

    if cmd in ("--version", "-V"):
        sys.stdout.write(f"claude-usage {VERSION}\n")
        sys.stdout.flush()
        return

    if cmd in ("--help", "-h"):
        sys.stdout.write(f"""\
claude-usage {VERSION} — Claude Code usage for tmux status bar

USAGE
  claude-usage [COMMAND]

STATUS BAR COMMANDS
  (none) / short    Current mode display  (used in tmux status-right)
  cost              Cost display, one-time  (ignores toggle state)
  long              Full breakdown: rate limits + token cost
  json              Structured JSON output

INTERACTIVE COMMANDS
  toggle            Switch percent ↔ cost display  [<prefix>+U in tmux]
  dashboard         Full-screen popup dashboard     [<prefix>+B in tmux]

UTILITY
  --refresh         Force one Anthropic API call and update cache
  --install-hook    Add Claude Code Stop hook to ~/.claude/settings.json
  --uninstall-hook  Remove Claude Code Stop hook
  --version, -V     Show version and exit
  --help,    -h     Show this help

SETTINGS  (~/.claude/tmux-claude-status.json)
  realtime   false    true = poll API every cache_ttl seconds (costs tokens)
  cache_ttl  300      Cache TTL in seconds
  provider   "auto"   auto | anthropic | bedrock | other

TMUX KEYBINDINGS  (configured by install.sh / TPM)
  <prefix>+U   Toggle percent ↔ cost
  <prefix>+B   Open dashboard popup  (requires tmux 3.2+)

MORE INFO
  https://github.com/long-910/tmux-claude-status
""")
        sys.stdout.flush()
        return

    if cmd == "--refresh":
        data = fetch_rate_limit()
        if data and "_error" not in data:
            save_cache(data)
            sys.stdout.write(f"5h={fmt_pct(data['util_5h'])} 7d={fmt_pct(data['util_7d'])}\n")
            sys.stdout.flush()
        else:
            err = data.get("_error", "unknown") if data else "no token (check: claude auth status)"
            body = data.get("_body", "") if data else ""
            detail = f"\n       {body}" if body else ""
            sys.stderr.write(f"[ERROR] API fetch failed: {err}{detail}\n")
        return

    if cmd == "--install-hook":
        install_hook()
        return

    if cmd == "--uninstall-hook":
        uninstall_hook()
        return

    if cmd == "toggle":
        new = toggle_display_mode()
        sys.stdout.write(f"mode -> {new}\n")
        sys.stdout.flush()
        return

    if cmd in ("short", ""):
        settings = load_settings()
        provider = detect_provider(settings)
        if provider == "other":
            # Bedrock / API key: rate-limit headers unavailable → show cost
            out = "[cost] " + short_cost(load_jsonl_records())
        else:
            mode = get_display_mode()
            if mode == "cost":
                out = "[cost] " + short_cost(load_jsonl_records())
            else:
                rl = get_rate_limit()
                if rl and "_error" not in rl:
                    out = short_percent(rl)
                elif rl and "_error" in rl:
                    code = re.search(r'\b(\d{3})\b', rl["_error"])
                    tag = code.group(1) if code else "ERR"
                    out = f"[ERR:{tag}]"
                else:
                    out = "[ERR:NO_DATA]"
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
        return

    if cmd == "cost":
        out = short_cost(load_jsonl_records())
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
        return

    if cmd == "long":
        s = load_settings()
        sys.stdout.write(long_output(get_rate_limit(), load_jsonl_records(), s) + "\n")
        sys.stdout.flush()
        return

    if cmd == "dashboard":
        dashboard_cmd()
        return

    if cmd == "json":
        settings = load_settings()
        provider = detect_provider(settings)
        rl = get_rate_limit() if provider == "anthropic" else None
        records = load_jsonl_records()
        now = datetime.now(timezone.utc)
        def w(since):
            t = aggregate(records, since)
            return {**t, "cost_usd": round(calc_cost(t), 6)}
        out = {
            "version":      VERSION,
            "provider":     provider,
            "rate_limit":   rl,
            "cost": {
                "5h":    w(now - timedelta(hours=5)),
                "today": w(datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)),
                "7d":    w(now - timedelta(days=7)),
            },
            "display_mode": get_display_mode(),
            "settings":     settings,
            "generated_at": now.isoformat(),
        }
        sys.stdout.write(json.dumps(out, indent=2) + "\n")
        sys.stdout.flush()
        return

    sys.stderr.write(f"Unknown command: {cmd!r}\nRun 'claude-usage --help' for usage.\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
