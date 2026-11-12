"""Reproducible QA for the rendered short: format, loop closure, safe band, motion.

Usage: .venv/bin/python qa_check.py build/same_hand_final.mp4
"""
import json, subprocess, sys

import numpy as np

W, H, FPS, TOTAL = 1080, 1920, 30, 1350
SAFE_TOP, SAFE_BOT = 250, 1440


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-show_entries",
        "stream=codec_name,width,height,r_frame_rate,nb_read_frames,sample_rate,channels"
        ":format=duration,size,bit_rate", "-of", "json", path])
    return json.loads(out)


def gray_frames(path, w=270, h=480):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-vf",
                                   f"scale={w}:{h}:flags=area,format=gray",
                                   "-f", "rawvideo", "-"])
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w)


def ssim(a, b):
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    a, b = a.astype(np.float64), b.astype(np.float64)
    ma, mb = a.mean(), b.mean()
    va, vb = a.var(), b.var()
    cov = ((a - ma) * (b - mb)).mean()
    return ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))


def main(path):
    info = probe(path)
    v = [s for s in info["streams"] if s["codec_name"] != "aac"][0]
    a = [s for s in info["streams"] if s["codec_name"] == "aac"]
    dur = float(info["format"]["duration"])
    checks = {
        "duration_45s": abs(dur - 45.0) < 0.15,
        "1080x1920": (v["width"], v["height"]) == (W, H),
        "fps_30": v["r_frame_rate"] == "30/1",
        "frames_1350": int(v.get("nb_read_frames", 0)) == TOTAL,
        "has_aac_audio": bool(a) and a[0].get("channels") == 2,
    }

    g = gray_frames(path)
    top, bot = int(SAFE_TOP / H * g.shape[1]), int(SAFE_BOT / H * g.shape[1])
    viol = 0
    for i in range(len(g)):
        rows = np.nonzero(g[i].max(axis=1) > 170)[0]
        if len(rows) and (rows.min() < top - 2 or rows.max() > bot + 2):
            viol += 1
    checks["safe_band_clear"] = viol == 0

    loop = ssim(g[0], g[-1])
    checks["loop_ssim_gt_0.98"] = loop > 0.98

    d = np.abs(np.diff(g[:, ::4, ::4].astype(np.int16), axis=0)).mean(axis=(1, 2))
    runs, cur = [], 0
    for x in d:
        if x < 0.02:
            cur += 1
        else:
            if cur > 20:
                runs.append(cur)
            cur = 0
    checks["no_static_holds_gt_20f"] = len(runs) == 0

    checks = {k: bool(v) for k, v in checks.items()}
    print(json.dumps({
        "file": path,
        "duration_s": round(dur, 2),
        "size_mb": round(int(info["format"]["size"]) / 1e6, 1),
        "video_bitrate_mbps": round(int(info["format"]["bit_rate"]) / 1e6, 2),
        "frames": int(v.get("nb_read_frames", 0)),
        "loop_ssim": round(float(loop), 4),
        "safe_band_violations": viol,
        "median_frame_delta": round(float(np.median(d)), 3),
        "longest_static_run_frames": max(runs) if runs else 0,
        "checks": checks,
        "all_pass": all(checks.values()),
    }, indent=2))
    return all(checks.values())


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else "build/same_hand_final.mp4") else 1)
