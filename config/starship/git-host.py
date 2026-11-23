#!/usr/bin/env python3
"""Show the provider of the current branch's remote, using local Git data only."""
import os
import re
import subprocess
from urllib.parse import urlsplit


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    return result.stdout.rstrip("\n") if result.returncode == 0 else ""


def provider_icon():
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD")
    entries = git("config", "--null", "--get-regexp", r"^(branch\..*\.(remote|merge)|remote\..*\.url)$")
    config = {}
    remotes = []
    for record in entries.split("\0"):
        key, separator, value = record.partition("\n")
        if separator:
            config[key] = value
            match = re.fullmatch(r"remote\.(.+)\.url", key)
            if match and match[1] not in remotes:
                remotes.append(match[1])
    remote = config.get(f"branch.{branch}.remote")
    if not branch or not config.get(f"branch.{branch}.merge") or remote == "." or remote not in remotes:
        return
    url = git("remote", "get-url", "--", remote)
    if "://" in url:
        try:
            host = urlsplit(url).hostname or ""
        except ValueError:
            return
    else:
        match = re.fullmatch(r"(?:[^/@:]+@)?([^/:]+):.+", url)
        host = match[1] if match else ""
    for provider, icon in (("gitlab", "\uf296"), ("github", "\uf09b")):
        if re.search(r"(?:^|[.-])" + provider + r"(?:[.-]|$)", host.lower()):
            return icon


def main():
    result = subprocess.run(
        ["starship", "module", "git_status"],
        env={**os.environ, "STARSHIP_SHELL": "fish"},
        capture_output=True, text=True, check=True,
    )
    status = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout).strip()
    icon = provider_icon() or ""
    if status:
        print(f"[{status}]" + (f" {icon}" if icon else ""))
    elif icon:
        print(icon)


if __name__ == "__main__":
    main()
