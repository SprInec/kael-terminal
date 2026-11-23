"""A Codex statusline provider using newline-delimited MCP over stdio."""

from functools import lru_cache
import json
import math
import shutil
import subprocess
import sys
import time
import unicodedata


URI = "ui://ada-usage-statusline/footer"
TOOL = {
    "name": "statusline",
    "title": "Ada · Usage meters",
    "description": "Show Git changes, the current model, and weekly and context capacity remaining.",
    "inputSchema": {"type": "object", "properties": {}},
    "_meta": {
        "openai/ui": {"entrypoints": [{"type": "statusline", "resourceUri": URI}]}
    },
}


# Charcoal surfaces and muted accents sampled from the shell prompt reference.
PANEL = "#1D1D1D"
BORDER = "#5D5D5D"
MODEL_GOLD = "#EFCC88"
FAST_GOLD = "#F6C85F"
MODEL_EFFORT = "#A89A7F"
WEEKLY = "#B6C7C1"
CONTEXT = "#8BCCA8"
TRACK = "#545454"
UNKNOWN = "#9A9A9A"
ADDED = "#62CA93"
REMOVED = "#F47880"
LOW = "#EFBE86"
CRITICAL = "#F1A2AE"
METER_GRADIENTS = {
    WEEKLY: ("#819A91", "#C9E1D8"),
    CONTEXT: ("#4A9873", "#B5E8CB"),
    LOW: ("#BB814B", "#FFD39E"),
    CRITICAL: ("#C26777", "#FFB4BF"),
}
BAR_CELLS = 5
FILL = "━"
HALF = "╸"
RAIL = "─"
WEEK_MINUTES = 7 * 24 * 60
EFFORT_LABELS = {"default": "def", "medium": "med", "minimal": "min"}
EFFORT_GRADIENTS = {
    "max": ("#EBBB81", "#F6D9A0"),
    "ultra": ("#BFACED", "#E5CDF8"),
}
WORD_JOINER = "\N{WORD JOINER}"
GIT_COMMAND = shutil.which("/usr/bin/git") or "git"


def text(value, color, weight="normal"):
    # Keep adjacent styled spans together even when the viewport clips the strip.
    value = " ".join(value.splitlines()).replace(" ", "\N{NO-BREAK SPACE}")
    value = value.replace("-", "-" + WORD_JOINER).replace("/", "/" + WORD_JOINER)
    return {
        "type": "text",
        "props": {"color": color, "weight": weight},
        "children": [value + WORD_JOINER if value else ""],
    }


def cell_width(value):
    return sum(
        2 if unicodedata.east_asian_width(character) in {"F", "W"} else 1
        for character in value
        if unicodedata.category(character) not in {"Cc", "Cf", "Mn", "Me"}
    )


def compact(value, width):
    if cell_width(value) <= width:
        return value
    value = value[:width - 1]
    while cell_width(value) >= width:
        value = value[:-1]
    return value.rstrip() + "…"


def git(cwd, *args):
    try:
        result = subprocess.run(
            [GIT_COMMAND, "--no-optional-locks", "-C", cwd, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=0.2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def diff_totals(diff):
    files = additions = deletions = 0
    records = iter(diff.split(b"\0"))
    for record in records:
        if not record:
            continue
        added, removed, name = record.split(b"\t", 2)
        if not name:
            # NUL-delimited rename records include the old and new filenames.
            next(records, None)
            next(records, None)
        files += 1
        additions += int(added) if added.isdigit() else 0
        deletions += int(removed) if removed.isdigit() else 0
    return files, additions, deletions


@lru_cache(maxsize=16)
def git_changes(cwd, refresh_window):
    diff = git(
        cwd, "diff", "--no-ext-diff", "--no-textconv", "--no-relative",
        "--numstat", "-z", "HEAD", "--",
    )
    return diff_totals(diff) if diff is not None else None


def remaining(used):
    if not isinstance(used, (int, float)) or not math.isfinite(used):
        return None
    return 100 - min(100, max(0, used))


def weekly_remaining(account):
    for limits in account.get("rate_limits", []):
        if limits.get("limit_id") != "codex":
            continue
        for key in ("primary_limit", "secondary_limit"):
            window = limits.get(key)
            if window and window.get("window_minutes") == WEEK_MINUTES:
                return remaining(window.get("used_percent"))
    return None


def mix_rgb(start, end, progress):
    rgb = tuple(round(low + (high - low) * progress) for low, high in zip(start, end))
    return "#%02X%02X%02X" % rgb


def gradient_spans(value, stops, weight="normal"):
    glyphs = []
    for character in value:
        if glyphs and (
            unicodedata.category(character) in {"Cf", "Mn", "Mc", "Me"}
            or glyphs[-1].endswith("\u200d")
        ):
            glyphs[-1] += character
        else:
            glyphs.append(character)

    start, end = (bytes.fromhex(stop[1:]) for stop in stops)
    for index, glyph in enumerate(glyphs):
        progress = index / (len(glyphs) - 1) if len(glyphs) > 1 else 0.5
        yield text(glyph, mix_rgb(start, end, progress), weight)


def meter(label, left, accent):
    units = 0
    if left is None:
        value = "—"
        color = UNKNOWN
    else:
        percent = math.floor(left + 0.5)
        units = math.floor(percent * 2 * BAR_CELLS / 100 + 0.5)
        if 0 < percent < 100:
            units = min(2 * BAR_CELLS - 1, max(1, units))
        value = f"{percent}%"
        color = CRITICAL if percent <= 10 else LOW if percent <= 25 else accent

    full_cells, half_cell = divmod(units, 2)
    fill = FILL * full_cells + HALF * half_cell
    track = RAIL * (BAR_CELLS - full_cells - half_cell)
    colored_fill = gradient_spans(fill, METER_GRADIENTS[color]) if fill else ()
    return (
        text(f"{label} ", accent),
        *colored_fill,
        text(track, TRACK),
        text(f" {value}", color, weight="bold"),
    )


def badge(*spans):
    return {
        "type": "row",
        "props": {"gap": 0, "background": PANEL, "wrap": "nowrap"},
        "children": [
            {
                "type": "text",
                "children": list(spans),
            },
        ],
    }


def git_badge(cwd):
    if not cwd:
        return None
    # The MCP host requests a frame every second. Refresh Git once per interval.
    changes = git_changes(cwd, int(time.monotonic() // 3))
    if changes is None:
        return None

    files, additions, deletions = changes
    spans = [text(str(files), UNKNOWN)]
    if files:
        spans.extend([
            text(" · ", BORDER),
            text(f"+{additions}", ADDED),
            text(f" -{deletions}", REMOVED),
        ])
    return badge(*spans)


def model_badge(name, effort, fast):
    name_spans = [text(name, MODEL_GOLD)]
    if fast:
        name_spans.insert(0, text("⚡", FAST_GOLD))

    stops = EFFORT_GRADIENTS.get(effort)
    if stops is None:
        caption = f"·{EFFORT_LABELS.get(effort, effort[:10])}" if effort else ""
        return badge(*name_spans, text(caption, MODEL_EFFORT))

    return {
        "type": "row",
        "props": {"gap": 1, "wrap": "nowrap"},
        "children": [
            badge(*name_spans),
            {
                "type": "text",
                "children": list(gradient_spans(effort.upper(), stops, weight="bold")),
            },
        ],
    }


def render(state):
    """Render the displayed thread's latest snapshot."""
    thread = state.get("thread", {})
    model = thread.get("model", {})
    name = compact(" ".join((model.get("display_name") or "Codex").split()), 20)
    effort = model.get("reasoning_level") or ("default" if model else None)
    fast = model.get("service_tier") == "fast"
    context = thread.get("usage", {}).get("context", {})
    cwd = thread.get("workspace", {}).get("cwd")
    weekly_left = weekly_remaining(state.get("account", {}))
    context_left = remaining(context.get("used_percentage"))

    return {
        "type": "row",
        "props": {"gap": 2, "wrap": "wrap"},
        "children": [
            badge(*meter("Wk", weekly_left, WEEKLY)),
            badge(*meter("Ctx", context_left, CONTEXT)),
            git_badge(cwd),
            model_badge(name, effort, fast),
        ],
    }


def respond(method, params):
    if method == "initialize":
        return {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "ada-usage-statusline", "version": "1.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [TOOL]}
    if method == "tools/call":
        if params.get("name") != TOOL["name"]:
            raise ValueError("Unknown tool name")
        return {
            "content": [{"type": "text", "text": f"The statusline resource is {URI}."}]
        }
    if method == "resources/list":
        return {
            "resources": [
                {"name": "footer", "uri": URI, "mimeType": "application/json"}
            ]
        }
    if method == "resources/templates/list":
        return {"resourceTemplates": []}
    if method == "resources/read":
        if params.get("uri") != URI:
            raise ValueError("Unknown resource URI")
        state = params.get("_meta", {}).get("com.openai/codex-statusline-state", {})
        return {
            "contents": [
                {
                    "uri": URI,
                    "mimeType": "application/json",
                    "text": json.dumps(render(state), ensure_ascii=False),
                }
            ]
        }
    raise KeyError(method)


def main():
    for line in sys.stdin.buffer:
        reply = {"jsonrpc": "2.0", "id": None}
        try:
            request = json.loads(line)
            if not isinstance(request, dict) or not isinstance(
                request.get("method"), str
            ):
                reply["error"] = {"code": -32600, "message": "Invalid request"}
            elif "id" not in request:
                continue
            else:
                reply["id"] = request["id"]
                reply["result"] = respond(request["method"], request.get("params", {}))
        except json.JSONDecodeError:
            reply["error"] = {"code": -32700, "message": "Parse error"}
        except KeyError:
            reply["error"] = {"code": -32601, "message": "Method not found"}
        except (TypeError, ValueError, AttributeError):
            reply["error"] = {"code": -32602, "message": "Invalid parameters"}
        print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
