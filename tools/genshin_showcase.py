#!/usr/bin/env python3
"""Read a public Genshin showcase from Enka; fail closed if inaccessible.

Usage: python tools/genshin_showcase.py --uid 654252915 --output genshin-showcase.json
No third-party Python dependencies or credentials required. Does not read full roster/inventory.
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://enka.network/api/uid/{uid}/"

def summarize(data, uid):
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
        equipment = entry.get("equipList") or []
        weapon = next((e for e in equipment if isinstance(e, dict) and e.get("weapon")), {})
        characters.append({
            "avatar_id": entry["avatarId"],
            "level": entry.get("propMap", {}).get("4001", {}).get("val"),
            "promote_level": entry.get("promoteLevel"),
            "talent_levels_raw": entry.get("skillLevelMap", {}),
            "weapon": {
                "item_id": weapon.get("itemId"),
                "level": weapon.get("weapon", {}).get("level"),
                "promote_level": weapon.get("weapon", {}).get("promoteLevel")
            } if weapon else None
        })
    return {
        "uid": uid,
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": API.format(uid=uid),
        "nickname": player.get("nickname"),
        "profile_level": player.get("level"),
        "characters": characters,
        "showcase_only": True,
        "note": "Raw IDs and talent skill keys require trusted game metadata before mapping to character/material names. Missing showcase characters do not imply unowned characters."
    }

def collect(uid, timeout=20):
    req = urllib.request.Request(API.format(uid=uid), headers={
        "User-Agent": "EVEATLAS-GenshinShowcaseProbe/0.1 (public showcase; manual validation)",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return summarize(json.load(response), uid)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uid", default=os.environ.get("GENSHIN_UID", "654252915"))
    parser.add_argument("--output", default="genshin-showcase.json")
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
    with open(args.output, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
        fp.write("\n")
    print(f"SHOWCASE_OK uid={args.uid} visible_characters={len(data['characters'])} output={args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
