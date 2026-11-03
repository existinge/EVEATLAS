#!/usr/bin/env python3
"""Fetch and normalize one public Genshin showcase from Enka.Network.

This collector is intentionally narrow:
- one explicitly supplied UID
- public showcase only (never claims full roster/inventory)
- no credentials
- respects Enka's returned TTL by fetching once per run
- enriches IDs with Enka's published metadata/localization

Usage:
  python tools/genshin_showcase.py --uid 654252915 \
    --output data/genshin/showcase.json --markdown data/genshin/showcase.md
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

API = "https://enka.network/api/uid/{uid}/"
CHARACTERS_URL = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/characters.json"
LOC_URL = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/loc.json"

USER_AGENT = "EVEATLAS-GenshinShowcaseCollector/0.2 (single public UID; github.com/existinge/EVEATLAS)"


def fetch_json(url: str, timeout: int = 25):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def _name_from_hash(localizations, value):
    if value is None:
        return None
    return (localizations.get("en") or {}).get(str(value))


def _talents(entry, character_meta):
    levels = entry.get("skillLevelMap") or {}
    order = character_meta.get("SkillOrder") or []
    labels = ("normal", "skill", "burst")
    out = {}
    for label, skill_id in zip(labels, order):
        value = levels.get(str(skill_id), levels.get(skill_id))
        if value is not None:
            out[label] = int(value)
    return out


def _weapon(entry, localizations):
    equipment = entry.get("equipList") or []
    weapon = next(
        (e for e in equipment if isinstance(e, dict) and isinstance(e.get("weapon"), dict)),
        None,
    )
    if not weapon:
        return None

    weapon_data = weapon["weapon"]
    flat = weapon.get("flat") or {}
    affix = weapon_data.get("affixMap") or {}
    refinement = None
    if affix:
        try:
            refinement = max(int(v) for v in affix.values()) + 1
        except (TypeError, ValueError):
            refinement = None

    return {
        "item_id": weapon.get("itemId"),
        "name": _name_from_hash(localizations, flat.get("nameTextMapHash")),
        "level": weapon_data.get("level"),
        "promote_level": weapon_data.get("promoteLevel"),
        "refinement": refinement,
    }


def _artifact_sets(entry, localizations):
    counts = collections.Counter()
    for equip in entry.get("equipList") or []:
        if not isinstance(equip, dict) or "reliquary" not in equip:
            continue
        flat = equip.get("flat") or {}
        name = _name_from_hash(localizations, flat.get("setNameTextMapHash"))
        if name:
            counts[name] += 1
    return dict(sorted(counts.items()))


def summarize(data, uid, characters_meta, localizations):
    if not isinstance(data, dict):
        raise ValueError("Unexpected response: object required")

    player = data.get("playerInfo")
    if not isinstance(player, dict):
        raise ValueError("No playerInfo returned; showcase could not be verified")

    avatars = data.get("avatarInfoList", [])
    if not isinstance(avatars, list):
        raise ValueError("Invalid avatarInfoList")

    characters = []
    for entry in avatars:
        if not isinstance(entry, dict) or not isinstance(entry.get("avatarId"), int):
            continue

        avatar_id = str(entry["avatarId"])
        meta = characters_meta.get(avatar_id) or {}
        name = _name_from_hash(localizations, meta.get("NameTextMapHash"))
        if not name:
            side = meta.get("SideIconName") or ""
            name = side.removeprefix("UI_AvatarIcon_Side_") or f"Avatar {avatar_id}"

        level_raw = (entry.get("propMap") or {}).get("4001", {}).get("val")
        try:
            level = int(level_raw)
        except (TypeError, ValueError):
            level = None

        characters.append(
            {
                "avatar_id": int(avatar_id),
                "name": name,
                "level": level,
                "constellation": len(entry.get("talentIdList") or []),
                "talents": _talents(entry, meta),
                "weapon": _weapon(entry, localizations),
                "artifact_sets": _artifact_sets(entry, localizations),
            }
        )

    return {
        "uid": uid,
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": API.format(uid=uid),
        "ttl_seconds": data.get("ttl"),
        "profile": {
            "nickname": player.get("nickname"),
            "adventure_rank": player.get("level"),
            "world_level": player.get("worldLevel"),
        },
        "characters": characters,
        "showcase_only": True,
        "note": (
            "Enka returns only the in-game Character Showcase. Characters absent here may still be owned. "
            "Inventory quantities, Fragile Resin, and unshown builds are unknown."
        ),
    }


def render_markdown(data):
    profile = data["profile"]
    lines = [
        "# Genshin Showcase Snapshot",
        "",
        f"- UID: `{data['uid']}`",
        f"- Nickname: {profile.get('nickname') or 'Unknown'}",
        f"- Adventure Rank: {profile.get('adventure_rank') or 'Unknown'}",
        f"- Fetched: {data['fetched_at_utc']}",
        "- Scope: **public Character Showcase only** — not the full roster or inventory.",
        "",
        "| Character | Lv | C | Talents N / E / Q | Weapon | Weapon Lv | Artifact sets |",
        "|---|---:|---:|---|---|---:|---|",
    ]
    for c in data["characters"]:
        t = c.get("talents") or {}
        talent_text = f"{t.get('normal','?')} / {t.get('skill','?')} / {t.get('burst','?')}"
        w = c.get("weapon") or {}
        sets = ", ".join(f"{name} ×{count}" for name, count in (c.get("artifact_sets") or {}).items()) or "—"
        lines.append(
            f"| {c['name']} | {c.get('level') or '?'} | C{c.get('constellation',0)} | "
            f"{talent_text} | {w.get('name') or w.get('item_id') or '—'} | "
            f"{w.get('level') or '—'} | {sets} |"
        )
    lines.extend(["", f"Source: {data['source']}", ""])
    return "\n".join(lines)


def collect(uid, timeout=25):
    # One UID call per run. Metadata comes from Enka's public GitHub data store.
    showcase = fetch_json(API.format(uid=uid), timeout=timeout)
    characters_meta = fetch_json(CHARACTERS_URL, timeout=timeout)
    localizations = fetch_json(LOC_URL, timeout=timeout)
    return summarize(showcase, uid, characters_meta, localizations)


def _write(path, content):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uid", default=os.environ.get("GENSHIN_UID", "654252915"))
    parser.add_argument("--output", default="data/genshin/showcase.json")
    parser.add_argument("--markdown", default="data/genshin/showcase.md")
    args = parser.parse_args()

    if not (args.uid.isascii() and args.uid.isdigit() and len(args.uid) == 9):
        parser.error("UID must be nine digits")

    try:
        data = collect(args.uid)
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.HTTPError) as exc:
        print(f"SHOWCASE_FETCH_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if not data["characters"]:
        print("SHOWCASE_EMPTY: no visible character details; refusing to claim success", file=sys.stderr)
        return 2

    _write(args.output, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    _write(args.markdown, render_markdown(data))

    names = ", ".join(c["name"] for c in data["characters"])
    print(
        f"SHOWCASE_OK uid={args.uid} visible_characters={len(data['characters'])} "
        f"output={args.output}"
    )
    print(f"CHARACTERS: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
