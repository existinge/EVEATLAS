#!/usr/bin/env python3
"""Read-only YouTube Music listening snapshot for Japanese immersion.

Install: python -m pip install ytmusicapi
Authenticate locally per https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html
Run: python tools/ytmusic_immersion.py --auth ~/.config/eveatlas/ytmusic/browser.json --output ~/ytmusic-immersion.json
Do NOT commit authentication files or private listening exports to this public repo.
"""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def make_snapshot(history):
    """Produce a small, deliberately non-sensitive metadata snapshot.

    Language cannot be inferred reliably from song titles or artist names;
    mark candidates for user review rather than claiming songs are Japanese.
    """
    items = []
    for song in history:
        artists = song.get("artists") or []
        names = [a.get("name", "") for a in artists if isinstance(a, dict)]
        items.append({
            "title": song.get("title", ""),
            "artists": names,
            "video_id": song.get("videoId"),
            "played": song.get("played", ""),
            "language": "unverified",
        })
    counts = Counter((s["title"], tuple(s["artists"])) for s in items)
    repeats = [
        {"title": title, "artists": list(artists), "count_in_snapshot": count}
        for (title, artists), count in counts.most_common(15)
        if count > 1
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ytmusicapi.get_history",
        "scope_note": "Returned history is limited by YouTube Music; not a complete play log.",
        "songs": items,
        "repeats": repeats,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auth", type=Path, required=True, help="Local ytmusicapi browser authentication JSON")
    parser.add_argument("--output", type=Path, required=True, help="Private output JSON path outside repository")
    args = parser.parse_args()
    if not args.auth.is_file():
        parser.error("Authentication file missing; set up ytmusicapi locally first.")
    if args.output.resolve() == args.auth.resolve():
        parser.error("Output must not overwrite authentication.")
    from ytmusicapi import YTMusic
    snapshot = make_snapshot(YTMusic(str(args.auth.expanduser())).get_history())
    target = args.output.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with target.open("x", encoding="utf-8") as file:
        json.dump(snapshot, file, ensure_ascii=False, indent=2)
    target.chmod(0o600)
    print(f"Saved {len(snapshot['songs'])} song records to {target}. Review before sharing.")


if __name__ == "__main__":
    main()
