# -*- coding: utf-8 -*-
"""kb_index.py — batch.json 追加进本地知识库 INDEX.jsonl
用法：python kb_index.py --batch batch.json --index INDEX.jsonl --start-id 100
"""
import argparse, json, os, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--start-id", type=int, default=100)
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    args = ap.parse_args()

    batch = json.load(open(args.batch, encoding="utf-8"))
    existing = ""
    if os.path.exists(args.index):
        existing = open(args.index, encoding="utf-8").read()
    added = 0
    with open(args.index, "a", encoding="utf-8") as f:
        for i, r in enumerate(batch):
            kid = "kb-%03d" % (args.start_id + i)
            if r["modal_id"] in existing:  # 按 modal_id 防重复
                continue
            f.write(json.dumps({
                "id": kid, "date": args.date, "platform": "douyin",
                "source": "likes " + str(r["modal_id"]), "title": r["desc"][:80],
                "project_lines": [], "rating": r["level"],
                "summary": r["desc"][:150], "insights": r.get("hit_tags", [])
            }, ensure_ascii=False) + "\n")
            added += 1
    print("added %d entries -> %s" % (added, args.index))

if __name__ == "__main__":
    main()
