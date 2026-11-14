#!/usr/bin/env python3
"""Fetch the Artlist sound bank from S3 into `assets/audio/`.

The licensed masters are **not** committed to this repo (it is public, and the
Artlist licence does not permit redistributing the raw files). Only
`assets/audio/manifest.json` is tracked; this script materialises the audio it
describes.

    python tools/fetch_audio.py                 # fetch anything missing/damaged
    python tools/fetch_audio.py --force         # re-download everything
    python tools/fetch_audio.py --check         # verify only, no writes
    python tools/fetch_audio.py --bucket s3://other-bucket

Each object is copied to its slugged local path (`music/<slug>.mp3`,
`sfx/<slug>.aac`) and checked against the `size`/`bytes` recorded in the
manifest, so a truncated or stale object fails loudly instead of half-rendering.

Requires the AWS CLI on PATH and read access to the bucket (on the pokerfx EC2
the instance role `pokerfx-ec2-role` provides it).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets", "audio")
MANIFEST = os.path.join(ASSETS, "manifest.json")
DEFAULT_BUCKET = "s3://pokerfx-audio"


def entries(manifest):
    for group in ("music", "sfx"):
        for e in manifest.get(group, []):
            yield group, e


def expected_size(entry):
    for key in ("size", "bytes", "size_bytes"):
        if entry.get(key):
            return int(entry[key])
    return None


def s3_cp(bucket, key, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    subprocess.run(["aws", "s3", "cp", "--only-show-errors",
                    "%s/%s" % (bucket.rstrip("/"), key), tmp], check=True)
    os.replace(tmp, dest)


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--bucket", default=os.environ.get("POKERFX_AUDIO_BUCKET", DEFAULT_BUCKET))
    ap.add_argument("--force", action="store_true", help="re-download files that already exist")
    ap.add_argument("--check", action="store_true", help="verify only; never write")
    args = ap.parse_args()

    if not os.path.exists(MANIFEST):
        sys.exit("manifest not found: %s" % MANIFEST)
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)

    if not args.check and not shutil.which("aws"):
        sys.exit("aws CLI not found on PATH")

    fetched = skipped = failed = 0
    problems = []
    for group, e in entries(manifest):
        dest = os.path.join(ASSETS, e["file"])
        want = expected_size(e)
        have = os.path.getsize(dest) if os.path.exists(dest) else None

        if have is not None and want is not None and have == want and not args.force:
            skipped += 1
            continue
        if args.check:
            failed += 1
            problems.append("%-36s %s (have %s, want %s)" % (
                e["slug"], "missing" if have is None else "size mismatch", have, want))
            continue
        try:
            s3_cp(args.bucket, e["s3_key"], dest)
        except subprocess.CalledProcessError as exc:
            failed += 1
            problems.append("%-36s S3 copy failed (%s)" % (e["slug"], exc))
            continue
        got = os.path.getsize(dest)
        if want is not None and got != want:
            failed += 1
            problems.append("%-36s downloaded %d bytes, manifest says %d" % (e["slug"], got, want))
        else:
            fetched += 1
            print("  fetched %-36s %8d B" % (e["slug"], got), flush=True)

    total = sum(len(manifest.get(g, [])) for g in ("music", "sfx"))
    print("\n%d assets: %d fetched, %d already present, %d failed"
          % (total, fetched, skipped, failed))
    if problems:
        print("\nproblems:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
    if args.check and not problems:
        print("sound bank complete and intact")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
