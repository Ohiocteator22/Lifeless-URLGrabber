import json
import urllib.request
import urllib.error


def _parse_version(tag):
    """Turn 'v1.2.1' into (1, 2, 1). Ignores non-numeric suffixes."""
    if not tag:
        return (0,)
    tag = tag.lstrip("vV")
    parts = []
    for chunk in tag.split("."):
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts)


def check_for_update(current_version, owner, repo, timeout=6):
    """Return dict with keys: has_update, latest_tag, url, notes — or None."""
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        req = urllib.request.Request(
            api,
            headers={"User-Agent": "URLGrab-Updater"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    latest_tag = data.get("tag_name") or ""
    if not latest_tag:
        return None

    latest = _parse_version(latest_tag)
    current = _parse_version(current_version)
    if latest <= current:
        return None

    return {
        "has_update": True,
        "latest_tag": latest_tag,
        "url": data.get("html_url") or "",
        "notes": data.get("body") or "",
    }