# -*- coding: utf-8 -*-
"""rate_filter.py — 焦点标签评级筛选
读 likes_detail_*.json，按 config.focus_tags 与规则评级，产出 batch.json（A/B 级）。
评级：A=命中焦点标签且有干货信号 / B=命中但信息浅 / C=无关归档。
"""
import argparse, glob, json, os, re, sys

def load_config(path):
    if path and os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {"focus_tags": [], "whitelist_signals": ["教程", "原理", "方法论", "工具", "实战", "避坑", "测评", "开源", "案例"]}

def score(desc, tags, signals):
    hit_tags = [t for t in tags if t.lower() in desc.lower()]
    hit_sig = [s for s in signals if s in desc]
    return hit_tags, hit_sig

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("detail_dir")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--out", default="batch.json")
    args = ap.parse_args()
    cfg = load_config(args.config)
    tags, signals = cfg.get("focus_tags", []), cfg.get("whitelist_signals", [])

    rows = []
    for f in sorted(glob.glob(os.path.join(args.detail_dir, "likes_detail_*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        desc = j.get("desc", "") or ""
        hit_tags, hit_sig = score(desc, tags, signals)
        level = "A" if (hit_tags and hit_sig) else ("B" if hit_tags else ("C" if hit_sig else "D"))
        rows.append({"modal_id": j.get("modal_id"), "desc": desc[:200], "author": j.get("author", ""),
                     "hit_tags": hit_tags, "hit_signals": hit_sig, "level": level,
                     "file": os.path.basename(f)})

    ab = [r for r in rows if r["level"] in ("A", "B")]
    json.dump(ab, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(rows, open(args.out.replace(".json", "_all.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("evaluated %d | A=%d B=%d C/D=%d | batch -> %s" % (
        len(rows), sum(1 for r in rows if r['level']=='A'),
        sum(1 for r in rows if r['level']=='B'), len(rows)-len(ab), args.out))

if __name__ == "__main__":
    main()
